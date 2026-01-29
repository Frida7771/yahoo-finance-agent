"""
Real-time stock data via Alpaca WebSocket
"""
import asyncio
import json
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Store active WebSocket connections
active_connections: Set[WebSocket] = set()

# Alpaca WebSocket client
alpaca_ws = None
subscribed_symbols: Set[str] = set()


class AlpacaDataStream:
    """Alpaca real-time data stream manager"""
    
    def __init__(self):
        self.ws = None
        self.running = False
        self.settings = get_settings()
        
    async def connect(self):
        """Connect to Alpaca WebSocket"""
        if not self.settings.alpaca_api_key:
            logger.warning("Alpaca API key not configured")
            return False
            
        try:
            import websockets
            
            # Alpaca IEX (free) or SIP (paid) feed
            url = "wss://stream.data.alpaca.markets/v2/iex"
            
            self.ws = await websockets.connect(url)
            
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
        """Subscribe to real-time quotes for symbols"""
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
    
    async def listen(self):
        """Listen for incoming messages and broadcast to clients"""
        if not self.ws:
            return
            
        try:
            async for message in self.ws:
                data = json.loads(message)
                
                # Broadcast to all connected WebSocket clients
                if active_connections:
                    await broadcast(data)
                    
        except Exception as e:
            logger.error(f"Alpaca listen error: {e}")
            self.running = False
    
    async def close(self):
        """Close connection"""
        self.running = False
        if self.ws:
            await self.ws.close()


# Global Alpaca stream instance
alpaca_stream = AlpacaDataStream()


async def broadcast(data: dict):
    """Broadcast data to all connected clients"""
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
    
    # Start Alpaca connection if not running
    if not alpaca_stream.running:
        connected = await alpaca_stream.connect()
        if connected:
            # Start listening in background
            asyncio.create_task(alpaca_stream.listen())
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            action = data.get("action")
            symbols = data.get("symbols", [])
            
            # Normalize symbols to uppercase
            symbols = [s.upper() for s in symbols]
            
            if action == "subscribe" and symbols:
                await alpaca_stream.subscribe(symbols)
                await websocket.send_json({
                    "type": "subscribed",
                    "symbols": symbols
                })
                
            elif action == "unsubscribe" and symbols:
                await alpaca_stream.unsubscribe(symbols)
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
    
    return {
        "alpaca_configured": bool(settings.alpaca_api_key),
        "alpaca_connected": alpaca_stream.running,
        "active_connections": len(active_connections),
        "subscribed_symbols": list(subscribed_symbols)
    }

