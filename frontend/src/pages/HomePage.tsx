import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { UserMenu } from '@/components/UserMenu'
import { 
  TrendingUp, MessageSquare, LineChart, FileText, 
  BarChart3, Zap, Shield, ArrowRight, Github
} from 'lucide-react'

interface HomePageProps {
  onNavigateToAnalysis: (prefilledQuery?: string) => void
  onNavigateToQuotes: () => void
}

// Quick action items for Analysis page
const analysisFeatures = [
  {
    icon: TrendingUp,
    color: 'text-green-500',
    title: 'Stock Data',
    description: 'Real-time prices, historical data',
    query: 'Get the current stock price and key metrics for AAPL',
  },
  {
    icon: BarChart3,
    color: 'text-blue-500',
    title: 'Financials',
    description: 'Revenue, profit, ROE, valuation',
    query: 'Analyze the financials and valuation metrics for MSFT',
  },
  {
    icon: FileText,
    color: 'text-purple-500',
    title: 'SEC 10-K',
    description: 'Risk factors, legal, executives',
    query: 'What are the key risk factors for TSLA from their latest 10-K?',
  },
  {
    icon: Shield,
    color: 'text-orange-500',
    title: 'Investment Report',
    description: 'Full analysis with recommendation',
    query: 'Generate a comprehensive investment report for NVDA including valuation, risks, and recommendation',
  },
]

// Quick action items for Dashboard
const dashboardFeatures = [
  {
    icon: Zap,
    color: 'text-yellow-500',
    title: 'Live Quotes',
    description: 'WebSocket-powered real-time',
  },
  {
    icon: BarChart3,
    color: 'text-green-500',
    title: 'Mini Charts',
    description: 'TradingView integration',
  },
  {
    icon: TrendingUp,
    color: 'text-blue-500',
    title: 'Watchlists',
    description: 'Tech, Finance, Custom',
  },
  {
    icon: Shield,
    color: 'text-red-500',
    title: 'Price Alerts',
    description: 'Browser notifications',
  },
]

export function HomePage({ onNavigateToAnalysis, onNavigateToQuotes }: HomePageProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      {/* Top Navigation */}
      <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">📈</span>
            <span className="font-semibold">Finance Agent</span>
          </div>
          <UserMenu />
        </div>
      </header>

      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-grid-pattern opacity-5 pointer-events-none" />
        <div className="max-w-6xl mx-auto px-6 py-16">
          <div className="text-center space-y-6">
            <Badge variant="secondary" className="px-4 py-1">
              <Zap className="h-3 w-3 mr-1" />
              Powered by LangChain + Yahoo Finance
            </Badge>
            
            <h1 className="text-5xl md:text-6xl font-bold tracking-tight">
              <span className="text-primary">📈 Finance</span> Agent
            </h1>
            
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              AI-powered stock analysis with real-time market data, SEC filings, 
              and comprehensive financial insights — all through natural language.
            </p>

            <div className="flex justify-center gap-4 pt-4">
              <Button 
                size="lg" 
                onClick={() => onNavigateToAnalysis()} 
                className="gap-2 cursor-pointer hover:scale-105 transition-transform duration-200"
              >
                <MessageSquare className="h-5 w-5" />
                Start Analysis
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button 
                size="lg" 
                variant="outline" 
                onClick={onNavigateToQuotes} 
                className="gap-2 cursor-pointer hover:scale-105 hover:bg-green-500/10 hover:border-green-500/50 hover:text-green-500 transition-all duration-200"
              >
                <LineChart className="h-5 w-5" />
                Real-Time Dashboard
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-center mb-12">Choose Your Interface</h2>
        
        <div className="grid md:grid-cols-2 gap-8">
          {/* Analysis Card */}
          <Card className="overflow-hidden">
            <CardContent className="p-0">
              {/* Header */}
              <div 
                className="p-6 bg-primary/5 cursor-pointer hover:bg-primary/10 transition-colors"
                onClick={() => onNavigateToAnalysis()}
              >
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-xl bg-primary/10">
                    <MessageSquare className="h-8 w-8 text-primary" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold">AI Analysis</h3>
                    <p className="text-sm text-muted-foreground">Natural Language Interface</p>
                  </div>
                  <ArrowRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </div>

              {/* Clickable Feature Items */}
              <div className="divide-y">
                {analysisFeatures.map((feature) => (
                  <button
                    key={feature.title}
                    onClick={() => onNavigateToAnalysis(feature.query)}
                    className="w-full p-4 flex items-center gap-4 hover:bg-secondary/50 transition-colors text-left"
                  >
                    <feature.icon className={`h-5 w-5 ${feature.color}`} />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{feature.title}</p>
                      <p className="text-xs text-muted-foreground">{feature.description}</p>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      Try it →
                    </Badge>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Real-Time Dashboard Card */}
          <Card className="overflow-hidden">
            <CardContent className="p-0">
              {/* Header */}
              <div 
                className="p-6 bg-green-500/5 cursor-pointer hover:bg-green-500/10 transition-colors"
                onClick={onNavigateToQuotes}
              >
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-xl bg-green-500/10">
                    <LineChart className="h-8 w-8 text-green-500" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold">Real-Time Dashboard</h3>
                    <p className="text-sm text-muted-foreground">Live Market Data</p>
                  </div>
                  <ArrowRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </div>

              {/* Feature Items (not clickable with query, just navigates to dashboard) */}
              <div className="divide-y">
                {dashboardFeatures.map((feature) => (
                  <button
                    key={feature.title}
                    onClick={onNavigateToQuotes}
                    className="w-full p-4 flex items-center gap-4 hover:bg-secondary/50 transition-colors text-left"
                  >
                    <feature.icon className={`h-5 w-5 ${feature.color}`} />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{feature.title}</p>
                      <p className="text-xs text-muted-foreground">{feature.description}</p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Tech Stack */}
      <div className="max-w-6xl mx-auto px-6 py-16 border-t">
        <h2 className="text-xl font-semibold text-center mb-8">Built With</h2>
        <div className="flex flex-wrap justify-center gap-3">
          {['LangChain', 'LangGraph', 'FastAPI', 'React', 'TypeScript', 'Tailwind CSS', 'FAISS', 'Yahoo Finance', 'SEC EDGAR', 'Alpaca WebSocket'].map(tech => (
            <Badge key={tech} variant="outline" className="px-3 py-1">
              {tech}
            </Badge>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="max-w-6xl mx-auto px-6 flex justify-between items-center text-sm text-muted-foreground">
          <p>© 2025 Finance Agent. For educational purposes only.</p>
          <a 
            href="https://github.com/Frida7771/yahoo-finance-agent" 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center gap-2 hover:text-foreground transition-colors"
          >
            <Github className="h-4 w-4" />
            View on GitHub
          </a>
        </div>
      </footer>
    </div>
  )
}
