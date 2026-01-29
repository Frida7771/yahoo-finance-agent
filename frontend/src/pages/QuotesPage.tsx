import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  TrendingUp, TrendingDown, Wifi, WifiOff, Plus, X, 
  Bell, ArrowUpDown, LayoutGrid, List,
  ArrowLeft
} from 'lucide-react'

interface Quote {
  symbol: string
  price: number
  prevClose: number
  change: number
  changePercent: number
  high: number
  low: number
  volume: number
  timestamp: string
}

interface PriceAlert {
  symbol: string
  targetPrice: number
  direction: 'above' | 'below'
  triggered: boolean
}

interface Watchlist {
  name: string
  symbols: string[]
}

export function QuotesPage({ onBack }: { onBack: () => void }) {
  const [quotes, setQuotes] = useState<Record<string, Quote>>({})
  const [connected, setConnected] = useState(false)
  const [watchlists, setWatchlists] = useState<Watchlist[]>([
    { name: 'Tech', symbols: ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META'] },
    { name: 'Finance', symbols: ['JPM', 'BAC', 'GS', 'MS'] },
  ])
  const [activeWatchlist, setActiveWatchlist] = useState(0)
  const [alerts, setAlerts] = useState<PriceAlert[]>([])
  const [newSymbol, setNewSymbol] = useState('')
  const [sortBy, setSortBy] = useState<'symbol' | 'change'>('symbol')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [alertInput, setAlertInput] = useState<{ symbol: string; price: string; direction: 'above' | 'below' }>({ symbol: '', price: '', direction: 'above' })
  const wsRef = useRef<WebSocket | null>(null)

  const currentSymbols = watchlists[activeWatchlist]?.symbols || []

  useEffect(() => {
    connectWebSocket()
    return () => wsRef.current?.close()
  }, [])

  useEffect(() => {
    if (connected && currentSymbols.length > 0) {
      subscribeToSymbols(currentSymbols)
    }
  }, [connected, activeWatchlist])

  // Check price alerts
  useEffect(() => {
    alerts.forEach(alert => {
      const quote = quotes[alert.symbol]
      if (quote && !alert.triggered) {
        const triggered = alert.direction === 'above' 
          ? quote.price >= alert.targetPrice
          : quote.price <= alert.targetPrice
        
        if (triggered) {
          // Show notification
          if (Notification.permission === 'granted') {
            new Notification(`Price Alert: ${alert.symbol}`, {
              body: `${alert.symbol} is now $${quote.price.toFixed(2)} (${alert.direction} $${alert.targetPrice})`
            })
          }
          setAlerts(prev => prev.map(a => 
            a === alert ? { ...a, triggered: true } : a
          ))
        }
      }
    })
  }, [quotes, alerts])

  const connectWebSocket = () => {
    const devWsUrl = 'ws://localhost:8000/api/realtime/ws/quotes'
    const ws = new WebSocket(devWsUrl)
    
    ws.onopen = () => {
      setConnected(true)
      // Request notification permission
      if (Notification.permission === 'default') {
        Notification.requestPermission()
      }
    }
    
    ws.onclose = () => {
      setConnected(false)
      setTimeout(connectWebSocket, 3000)
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleMessage(data)
      } catch (e) {
        console.error('Failed to parse:', e)
      }
    }
    
    wsRef.current = ws
  }

  const handleMessage = (data: any) => {
    if (Array.isArray(data)) {
      data.forEach(item => {
        if (item.T === 't' || item.T === 'q') {
          const price = item.T === 't' ? item.p : (item.bp + item.ap) / 2
          setQuotes(prev => {
            const existing = prev[item.S] || {}
            const prevClose = existing.prevClose || price
            const change = price - prevClose
            const changePercent = (change / prevClose) * 100
            
            return {
              ...prev,
              [item.S]: {
                ...existing,
                symbol: item.S,
                price,
                prevClose,
                change,
                changePercent,
                high: Math.max(existing.high || price, price),
                low: Math.min(existing.low || price, price),
                volume: (existing.volume || 0) + (item.s || 0),
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
      wsRef.current.send(JSON.stringify({ action: 'subscribe', symbols }))
    }
  }

  const addSymbol = () => {
    const symbol = newSymbol.toUpperCase().trim()
    if (symbol && !currentSymbols.includes(symbol)) {
      setWatchlists(prev => prev.map((wl, i) => 
        i === activeWatchlist 
          ? { ...wl, symbols: [...wl.symbols, symbol] }
          : wl
      ))
      subscribeToSymbols([symbol])
      setNewSymbol('')
    }
  }

  const removeSymbol = (symbol: string) => {
    setWatchlists(prev => prev.map((wl, i) =>
      i === activeWatchlist
        ? { ...wl, symbols: wl.symbols.filter(s => s !== symbol) }
        : wl
    ))
  }

  const addAlert = () => {
    if (alertInput.symbol && alertInput.price) {
      setAlerts(prev => [...prev, {
        symbol: alertInput.symbol.toUpperCase(),
        targetPrice: parseFloat(alertInput.price),
        direction: alertInput.direction,
        triggered: false
      }])
      setAlertInput({ symbol: '', price: '', direction: 'above' })
    }
  }

  const sortedSymbols = [...currentSymbols].sort((a, b) => {
    if (sortBy === 'change') {
      const changeA = quotes[a]?.changePercent || 0
      const changeB = quotes[b]?.changePercent || 0
      return changeB - changeA
    }
    return a.localeCompare(b)
  })

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-2xl font-bold">📈 Real-Time Quotes</h1>
          <Badge variant={connected ? 'default' : 'secondary'}>
            {connected ? <><Wifi className="h-3 w-3 mr-1" /> Live</> : <><WifiOff className="h-3 w-3 mr-1" /> Offline</>}
          </Badge>
        </div>
        
        <div className="flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => setSortBy(sortBy === 'symbol' ? 'change' : 'symbol')}
          >
            <ArrowUpDown className="h-4 w-4" />
          </Button>
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
          >
            {viewMode === 'grid' ? <List className="h-4 w-4" /> : <LayoutGrid className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Main Content */}
        <div className="col-span-9">
          {/* Watchlist Tabs */}
          <div className="flex gap-2 mb-4">
            {watchlists.map((wl, i) => (
              <Button
                key={wl.name}
                variant={i === activeWatchlist ? 'default' : 'outline'}
                size="sm"
                onClick={() => setActiveWatchlist(i)}
              >
                {wl.name}
              </Button>
            ))}
            <Button variant="ghost" size="sm">
              <Plus className="h-4 w-4" />
            </Button>
          </div>

          {/* Add Symbol */}
          <div className="flex gap-2 mb-6">
            <Input
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
              placeholder="Add ticker (e.g., AAPL)"
              className="max-w-xs"
              onKeyDown={(e) => e.key === 'Enter' && addSymbol()}
            />
            <Button onClick={addSymbol}>
              <Plus className="h-4 w-4 mr-1" /> Add
            </Button>
          </div>

          {/* Quotes Grid/List */}
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-3 gap-4">
              {sortedSymbols.map(symbol => {
                const quote = quotes[symbol]
                const isUp = (quote?.changePercent || 0) >= 0
                
                return (
                  <Card key={symbol} className="relative overflow-hidden">
                    <button 
                      onClick={() => removeSymbol(symbol)}
                      className="absolute top-2 right-2 text-muted-foreground hover:text-foreground z-10"
                      title={`Remove ${symbol}`}
                      aria-label={`Remove ${symbol}`}
                    >
                      <X className="h-4 w-4" />
                    </button>
                    
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-lg font-bold">{symbol}</span>
                        <Badge variant={isUp ? 'default' : 'secondary'} className={isUp ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500'}>
                          {isUp ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
                          {quote?.changePercent?.toFixed(2) || '0.00'}%
                        </Badge>
                      </div>
                      
                      <div className="text-3xl font-mono font-bold mb-2">
                        ${quote?.price?.toFixed(2) || '---'}
                      </div>
                      
                      <div className={`text-sm ${isUp ? 'text-green-500' : 'text-red-500'}`}>
                        {isUp ? '+' : ''}{quote?.change?.toFixed(2) || '0.00'}
                      </div>
                      
                      {/* Mini Chart Placeholder - TradingView Widget */}
                      <div className="mt-4 h-16 bg-secondary/50 rounded flex items-center justify-center text-xs text-muted-foreground">
                        <iframe
                          src={`https://s.tradingview.com/embed-widget/mini-symbol-overview/?locale=en&symbol=${symbol}&width=100%25&height=100%25&dateRange=1D&colorTheme=dark&isTransparent=true&autosize=true`}
                          className="w-full h-full border-0"
                          title={`${symbol} chart`}
                        />
                      </div>
                      
                      <div className="grid grid-cols-2 gap-2 mt-4 text-xs text-muted-foreground">
                        <div>H: ${quote?.high?.toFixed(2) || '---'}</div>
                        <div>L: ${quote?.low?.toFixed(2) || '---'}</div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          ) : (
            <Card>
              <CardContent className="p-0">
                <table className="w-full">
                  <thead className="border-b">
                    <tr className="text-xs text-muted-foreground">
                      <th className="text-left p-3">Symbol</th>
                      <th className="text-right p-3">Price</th>
                      <th className="text-right p-3">Change</th>
                      <th className="text-right p-3">%</th>
                      <th className="text-right p-3">High</th>
                      <th className="text-right p-3">Low</th>
                      <th className="p-3"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedSymbols.map(symbol => {
                      const quote = quotes[symbol]
                      const isUp = (quote?.changePercent || 0) >= 0
                      
                      return (
                        <tr key={symbol} className="border-b hover:bg-secondary/50">
                          <td className="p-3 font-bold">{symbol}</td>
                          <td className="p-3 text-right font-mono">${quote?.price?.toFixed(2) || '---'}</td>
                          <td className={`p-3 text-right ${isUp ? 'text-green-500' : 'text-red-500'}`}>
                            {isUp ? '+' : ''}{quote?.change?.toFixed(2) || '0.00'}
                          </td>
                          <td className={`p-3 text-right ${isUp ? 'text-green-500' : 'text-red-500'}`}>
                            {quote?.changePercent?.toFixed(2) || '0.00'}%
                          </td>
                          <td className="p-3 text-right text-muted-foreground">${quote?.high?.toFixed(2) || '---'}</td>
                          <td className="p-3 text-right text-muted-foreground">${quote?.low?.toFixed(2) || '---'}</td>
                          <td className="p-3">
                            <Button variant="ghost" size="icon" onClick={() => removeSymbol(symbol)}>
                              <X className="h-3 w-3" />
                            </Button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar - Alerts */}
        <div className="col-span-3 space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Bell className="h-4 w-4" /> Price Alerts
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <Input
                  value={alertInput.symbol}
                  onChange={(e) => setAlertInput(prev => ({ ...prev, symbol: e.target.value.toUpperCase() }))}
                  placeholder="Symbol"
                  className="h-8"
                />
                <div className="flex gap-2">
                  <Input
                    value={alertInput.price}
                    onChange={(e) => setAlertInput(prev => ({ ...prev, price: e.target.value }))}
                    placeholder="Price"
                    type="number"
                    className="h-8"
                  />
                  <select
                    value={alertInput.direction}
                    onChange={(e) => setAlertInput(prev => ({ ...prev, direction: e.target.value as 'above' | 'below' }))}
                    className="h-8 px-2 rounded-md border bg-background text-sm"
                    title="Price direction"
                    aria-label="Price direction"
                  >
                    <option value="above">Above</option>
                    <option value="below">Below</option>
                  </select>
                </div>
                <Button size="sm" className="w-full" onClick={addAlert}>
                  Add Alert
                </Button>
              </div>
              
              <ScrollArea className="h-48">
                <div className="space-y-2">
                  {alerts.map((alert, i) => (
                    <div 
                      key={i}
                      className={`flex items-center justify-between p-2 rounded text-sm ${
                        alert.triggered ? 'bg-green-500/20' : 'bg-secondary/50'
                      }`}
                    >
                      <div>
                        <span className="font-medium">{alert.symbol}</span>
                        <span className="text-muted-foreground ml-1">
                          {alert.direction} ${alert.targetPrice}
                        </span>
                      </div>
                      {alert.triggered ? (
                        <Badge variant="default" className="bg-green-500">Triggered</Badge>
                      ) : (
                        <Button 
                          variant="ghost" 
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => setAlerts(prev => prev.filter((_, j) => j !== i))}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  ))}
                  {alerts.length === 0 && (
                    <p className="text-xs text-muted-foreground text-center py-4">
                      No alerts set
                    </p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Market Status</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Connection</span>
                <span className={connected ? 'text-green-500' : 'text-red-500'}>
                  {connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Watching</span>
                <span>{currentSymbols.length} symbols</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Alerts</span>
                <span>{alerts.filter(a => !a.triggered).length} active</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

