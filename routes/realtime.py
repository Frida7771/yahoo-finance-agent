"""
Real-time stock data via Alpaca WebSocket + Redis Stream

Architecture:
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Alpaca WS   │ ──► │ Redis Stream │ ──► │ Consumer        │
│ (1 reader)  │     │              │     │ (broadcast)     │
└─────────────┘     └──────────────┘     └─────────────────┘
                                                  │
                                                  ▼
                                         ┌───────────────┐
                                         │ WebSocket     │
                                         │ clients       │
                                         └───────────────┘
"""
import asyncio
import json
import logging
from typing import Set
from contextlib import asynccontextmanager

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Store active WebSocket connections
active_connections: Set[WebSocket] = set()
subscribed_symbols: Set[str] = set()

# Global instances
redis_client = None
alpaca_reader_task = None
redis_consumer_task = None


async def get_redis():
    """Get Redis client (lazy initialization)"""
    global redis_client
    if redis_client is None:
        try:
            import redis.asyncio as redis
            settings = get_settings()
            redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            # Test connection
            await redis_client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Falling back to in-memory mode.")
            redis_client = None
    return redis_client


class AlpacaReader:
    """
    Single reader that connects to Alpaca WebSocket and writes to Redis Stream.
    Only one instance should run at a time.
    """
    
    def __init__(self):
        self.ws = None
        self.running = False
        self.settings = get_settings()
        self._lock = asyncio.Lock()
        
    async def start(self):
        """Start the Alpaca reader (only one can run)"""
        async with self._lock:
            if self.running:
                return True
            return await self._connect()
    
    async def _connect(self):
        """Connect to Alpaca WebSocket"""
        if not self.settings.alpaca_api_key:
            logger.warning("Alpaca API key not configured")
            return False
            
        try:
            import websockets
            
            url = "wss://stream.data.alpaca.markets/v2/iex"
            
            self.ws = await websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5
            )
            
            # Authenticate
            auth_msg = {
                "action": "auth",
                "key": self.settings.alpaca_api_key,
                "secret": self.settings.alpaca_secret_key
            }
            await self.ws.send(json.dumps(auth_msg))
            
            response = await self.ws.recv()
            data = json.loads(response)
            logger.info(f"Alpaca auth response: {data}")
            
            self.running = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Alpaca: {e}")
            return False
    
    async def subscribe(self, symbols: list[str]):
        """Subscribe to symbols"""
        if not self.ws or not self.running:
            return
            
        try:
            sub_msg = {
                "action": "subscribe",
                "trades": symbols,
                "quotes": symbols
            }
            await self.ws.send(json.dumps(sub_msg))
            subscribed_symbols.update(symbols)
            logger.info(f"Subscribed to: {symbols}")
        except Exception as e:
            logger.error(f"Subscribe error: {e}")
    
    async def unsubscribe(self, symbols: list[str]):
        """Unsubscribe from symbols"""
        if not self.ws or not self.running:
            return
            
        try:
            unsub_msg = {
                "action": "unsubscribe",
                "trades": symbols,
                "quotes": symbols
            }
            await self.ws.send(json.dumps(unsub_msg))
            subscribed_symbols.difference_update(symbols)
            logger.info(f"Unsubscribed from: {symbols}")
        except Exception as e:
            logger.error(f"Unsubscribe error: {e}")
    
    async def read_and_publish(self):
        """Read from Alpaca and publish to Redis Stream"""
        redis = await get_redis()
        settings = self.settings
        reconnect_delay = 5
        max_reconnect_delay = 60  # Cap at 60 seconds
        consecutive_failures = 0
        
        while True:
            try:
                if not self.ws or not self.running:
                    # Check if market is likely closed (reduce log spam)
                    if consecutive_failures > 3:
                        logger.info(f"Multiple connection failures. Market may be closed. Retrying in {reconnect_delay}s...")
                    else:
                        logger.info("Reconnecting to Alpaca...")
                    
                    await asyncio.sleep(reconnect_delay)
                    connected = await self._connect()
                    
                    if connected:
                        consecutive_failures = 0
                        reconnect_delay = 5  # Reset delay
                        if subscribed_symbols:
                            await self.subscribe(list(subscribed_symbols))
                    else:
                        consecutive_failures += 1
                        # Exponential backoff, capped at max_reconnect_delay
                        reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)
                    continue
                
                # Read message from Alpaca (with timeout)
                message = await asyncio.wait_for(self.ws.recv(), timeout=30)
                data = json.loads(message)
                consecutive_failures = 0  # Reset on successful message
                
                # Publish to Redis Stream or broadcast directly
                if redis:
                    # Write to Redis Stream
                    await redis.xadd(
                        settings.redis_stream_name,
                        {"data": json.dumps(data)},
                        maxlen=10000  # Keep last 10k messages
                    )
                else:
                    # Fallback: broadcast directly (in-memory mode)
                    await broadcast(data)
                    
            except asyncio.TimeoutError:
                # No data received for 30s - likely market closed or no subscriptions
                if subscribed_symbols:
                    logger.debug("No data received (market may be closed)")
                continue
            except asyncio.CancelledError:
                logger.info("Alpaca reader cancelled")
                break
            except Exception as e:
                error_msg = str(e)
                # Reduce log spam for known disconnection errors
                if "no close frame" in error_msg or "connection closed" in error_msg.lower():
                    if consecutive_failures == 0:
                        logger.warning(f"Alpaca connection lost: {e}")
                else:
                    logger.warning(f"Alpaca reader error: {e}")
                
                self.running = False
                consecutive_failures += 1
                reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)
                await asyncio.sleep(reconnect_delay)
    
    async def close(self):
        """Close connection"""
        self.running = False
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass


class RedisConsumer:
    """
    Consumer that reads from Redis Stream and broadcasts to WebSocket clients.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.running = False
        self.consumer_name = f"consumer-{id(self)}"
        
    async def start(self):
        """Start consuming from Redis Stream"""
        redis = await get_redis()
        if not redis:
            logger.info("Redis not available, skipping consumer")
            return
            
        settings = self.settings
        stream_name = settings.redis_stream_name
        group_name = settings.redis_consumer_group
        
        # Create consumer group if not exists
        try:
            await redis.xgroup_create(stream_name, group_name, id="0", mkstream=True)
            logger.info(f"Created consumer group: {group_name}")
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                logger.error(f"Failed to create consumer group: {e}")
        
        self.running = True
        logger.info(f"Redis consumer started: {self.consumer_name}")
        
        while self.running:
            try:
                # Read from stream with consumer group
                messages = await redis.xreadgroup(
                    group_name,
                    self.consumer_name,
                    {stream_name: ">"},  # Read only new messages
                    count=100,
                    block=1000  # Block for 1 second
                )
                
                if messages:
                    for stream, entries in messages:
                        for msg_id, fields in entries:
                            data = json.loads(fields["data"])
                            
                            # Broadcast to all WebSocket clients
                            await broadcast(data)
                            
                            # Acknowledge message
                            await redis.xack(stream_name, group_name, msg_id)
                            
            except asyncio.CancelledError:
                logger.info("Redis consumer cancelled")
                break
            except Exception as e:
                logger.error(f"Redis consumer error: {e}")
                await asyncio.sleep(1)
        
        self.running = False
    
    def stop(self):
        """Stop consumer"""
        self.running = False


# Global instances
alpaca_reader = AlpacaReader()
redis_consumer = RedisConsumer()


async def broadcast(data: dict):
    """Broadcast data to all connected WebSocket clients"""
    if not active_connections:
        return
        
    message = json.dumps(data)
    disconnected = set()
    
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except:
            disconnected.add(connection)
    
    # Remove disconnected clients
    active_connections.difference_update(disconnected)


async def start_background_tasks():
    """Start Alpaca reader and Redis consumer"""
    global alpaca_reader_task, redis_consumer_task
    
    # Start Alpaca reader (only if not already running)
    if alpaca_reader_task is None or alpaca_reader_task.done():
        connected = await alpaca_reader.start()
        if connected:
            alpaca_reader_task = asyncio.create_task(alpaca_reader.read_and_publish())
            logger.info("Alpaca reader task started")
    
    # Start Redis consumer (only if Redis is available and not already running)
    redis = await get_redis()
    if redis and (redis_consumer_task is None or redis_consumer_task.done()):
        redis_consumer_task = asyncio.create_task(redis_consumer.start())
        logger.info("Redis consumer task started")


@router.websocket("/ws/quotes")
async def websocket_quotes(websocket: WebSocket):
    """
    WebSocket endpoint for real-time stock quotes.
    
    Client can send:
    - {"action": "subscribe", "symbols": ["AAPL", "MSFT"]}
    - {"action": "unsubscribe", "symbols": ["AAPL"]}
    """
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"Client connected. Total connections: {len(active_connections)}")
    
    settings = get_settings()
    
    # Check if Alpaca is configured
    if not settings.alpaca_api_key:
        await websocket.send_json({
            "type": "error",
            "message": "Alpaca API not configured. Add ALPACA_API_KEY and ALPACA_SECRET_KEY to .env"
        })
    
    # Start background tasks if needed
    await start_background_tasks()
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            symbols = data.get("symbols", [])
            symbols = [s.upper() for s in symbols]
            
            if action == "subscribe" and symbols:
                await alpaca_reader.subscribe(symbols)
                await websocket.send_json({
                    "type": "subscribed",
                    "symbols": symbols
                })
                
            elif action == "unsubscribe" and symbols:
                await alpaca_reader.unsubscribe(symbols)
                await websocket.send_json({
                    "type": "unsubscribed", 
                    "symbols": symbols
                })
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.discard(websocket)
        logger.info(f"Connection closed. Total connections: {len(active_connections)}")


@router.get("/realtime/status")
async def realtime_status():
    """Check real-time data connection status"""
    settings = get_settings()
    redis = await get_redis()
    
    return {
        "alpaca_configured": bool(settings.alpaca_api_key),
        "alpaca_connected": alpaca_reader.running,
        "redis_connected": redis is not None,
        "redis_consumer_running": redis_consumer.running,
        "active_connections": len(active_connections),
        "subscribed_symbols": list(subscribed_symbols)
    }
