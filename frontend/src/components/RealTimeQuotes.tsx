import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { TrendingUp, TrendingDown, Wifi, WifiOff, Plus, X } from 'lucide-react'

interface Quote {
  symbol: string
  price: number
  change: number
  changePercent: number
  timestamp: string
}

export function RealTimeQuotes() {
  const [quotes, setQuotes] = useState<Record<string, Quote>>({})
  const [connected, setConnected] = useState(false)
  const [watchlist, setWatchlist] = useState<string[]>(['AAPL', 'MSFT', 'NVDA'])
  const [newSymbol, setNewSymbol] = useState('')
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    connectWebSocket()
    return () => {
      wsRef.current?.close()
    }
  }, [])

  useEffect(() => {
    if (connected && watchlist.length > 0) {
      subscribeToSymbols(watchlist)
    }
  }, [connected, watchlist])

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/realtime/ws/quotes`
    
    // For development, connect to backend directly
    const devWsUrl = 'ws://localhost:8000/api/realtime/ws/quotes'
    
    const ws = new WebSocket(window.location.port === '5173' ? devWsUrl : wsUrl)
    
    ws.onopen = () => {
      setConnected(true)
      console.log('WebSocket connected')
    }
    
    ws.onclose = () => {
      setConnected(false)
      console.log('WebSocket disconnected')
      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000)
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleMessage(data)
      } catch (e) {
        console.error('Failed to parse message:', e)
      }
    }
    
    wsRef.current = ws
  }

  const handleMessage = (data: any) => {
    // Handle different message types from Alpaca
    if (Array.isArray(data)) {
      data.forEach(item => {
        if (item.T === 't') {
          // Trade message
          setQuotes(prev => ({
            ...prev,
            [item.S]: {
              symbol: item.S,
              price: item.p,
              change: 0,
              changePercent: 0,
              timestamp: item.t
            }
          }))
        } else if (item.T === 'q') {
          // Quote message (bid/ask)
          setQuotes(prev => {
            const existing = prev[item.S]
            return {
              ...prev,
              [item.S]: {
                ...existing,
                symbol: item.S,
                price: (item.bp + item.ap) / 2, // Mid price
                timestamp: item.t
              }
            }
          })
        }
      })
    }
  }

  const subscribeToSymbols = (symbols: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        symbols
      }))
    }
  }

  const unsubscribeFromSymbol = (symbol: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        symbols: [symbol]
      }))
    }
    setWatchlist(prev => prev.filter(s => s !== symbol))
  }

  const addSymbol = () => {
    const symbol = newSymbol.toUpperCase().trim()
    if (symbol && !watchlist.includes(symbol)) {
      setWatchlist(prev => [...prev, symbol])
      setNewSymbol('')
    }
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            📈 Real-Time Quotes
          </CardTitle>
          <Badge variant={connected ? 'default' : 'secondary'} className="text-xs">
            {connected ? (
              <><Wifi className="h-3 w-3 mr-1" /> Live</>
            ) : (
              <><WifiOff className="h-3 w-3 mr-1" /> Offline</>
            )}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Add symbol input */}
        <div className="flex gap-2">
          <Input
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
            placeholder="Add ticker..."
            className="h-8 text-xs"
            onKeyDown={(e) => e.key === 'Enter' && addSymbol()}
          />
          <Button size="sm" onClick={addSymbol} className="h-8 px-2">
            <Plus className="h-3 w-3" />
          </Button>
        </div>
        
        {/* Quotes list */}
        <div className="space-y-2">
          {watchlist.map(symbol => {
            const quote = quotes[symbol]
            const isUp = quote?.change >= 0
            
            return (
              <div 
                key={symbol}
                className="flex items-center justify-between p-2 rounded-lg bg-secondary/50"
              >
                <div className="flex items-center gap-2">
                  <button 
                    onClick={() => unsubscribeFromSymbol(symbol)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-3 w-3" />
                  </button>
                  <span className="font-medium text-sm">{symbol}</span>
                </div>
                
                {quote ? (
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm">
                      ${quote.price.toFixed(2)}
                    </span>
                    <span className={`flex items-center text-xs ${isUp ? 'text-green-500' : 'text-red-500'}`}>
                      {isUp ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    </span>
                  </div>
                ) : (
                  <span className="text-xs text-muted-foreground">Loading...</span>
                )}
              </div>
            )
          })}
        </div>
        
        {!connected && (
          <p className="text-xs text-muted-foreground text-center">
            Configure ALPACA_API_KEY in .env for live data
          </p>
        )}
      </CardContent>
    </Card>
  )
}

