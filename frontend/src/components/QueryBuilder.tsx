import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Zap, TrendingUp, FileText } from 'lucide-react'

interface QueryBuilderProps {
  onQueryGenerated: (query: string) => void
}

const marketTags = [
  { id: 'price', label: 'Price', icon: '💰' },
  { id: 'financials', label: 'Financials', icon: '📊' },
  { id: 'valuation', label: 'Valuation', icon: '📈' },
  { id: 'analysis', label: 'Analysis', icon: '🔍' },
  { id: 'news', label: 'News', icon: '📰' },
  { id: 'recommendations', label: 'Ratings', icon: '👍' },
]

const secTags = [
  { id: 'risks', label: 'Risks', icon: '⚠️' },
  { id: 'business', label: 'Business', icon: '🏢' },
  { id: 'legal', label: 'Legal', icon: '⚖️' },
  { id: 'executives', label: 'Executives', icon: '👔' },
  { id: 'compensation', label: 'Pay', icon: '💵' },
  { id: 'cybersecurity', label: 'Cyber', icon: '🔒' },
]

const typeMap: Record<string, string> = {
  price: 'current stock price and trading data',
  financials: 'financial statements (revenue, profit, margins)',
  valuation: 'valuation metrics (PE, PB, EV/EBITDA)',
  analysis: 'comprehensive stock analysis',
  news: 'latest news and developments',
  recommendations: 'analyst recommendations and price targets',
  risks: 'risk factors from SEC 10-K filing',
  business: 'business description from SEC 10-K',
  legal: 'legal proceedings and lawsuits from SEC filing',
  executives: 'directors and executive officers from SEC filing',
  compensation: 'executive compensation from SEC filing',
  cybersecurity: 'cybersecurity disclosures from SEC filing',
}

export function QueryBuilder({ onQueryGenerated }: QueryBuilderProps) {
  const [ticker, setTicker] = useState('AAPL')
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set(['price']))

  const toggleTag = (tagId: string) => {
    const newSelected = new Set(selectedTags)
    if (newSelected.has(tagId)) {
      newSelected.delete(tagId)
    } else {
      newSelected.add(tagId)
    }
    setSelectedTags(newSelected)
  }

  const generateQuery = () => {
    const parts = Array.from(selectedTags)
      .map(id => typeMap[id])
      .filter(Boolean)

    let query = ''
    if (parts.length === 0) {
      query = `Tell me about ${ticker} stock`
    } else if (parts.length === 1) {
      query = `What is ${ticker}'s ${parts[0]}?`
    } else {
      query = `Analyze ${ticker}: show me ${parts.join(', ')}`
    }
    
    onQueryGenerated(query)
  }

  const quickTemplates = [
    { label: 'Full Analysis', query: `Give me a comprehensive analysis of ${ticker} including: current price, valuation (PE, PB), profitability (ROE, margins), financial health, analyst recommendations, and key risks.` },
    { label: 'Compare', query: `Compare ${ticker} with its main competitors. Show valuation metrics, profitability, and growth rates.` },
    { label: 'Research Report', query: `Create an investment research report for ${ticker}. Include company overview, financial analysis, valuation assessment, risk factors from SEC filings, and investment recommendation.` },
  ]

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2 text-primary">
            <Zap className="h-4 w-4" />
            Query Builder
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-xs text-muted-foreground mb-1.5 block">Stock Ticker</label>
            <Input
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="e.g. AAPL, MSFT"
              className="h-8"
            />
          </div>
          
          <div>
            <label className="text-xs text-muted-foreground mb-1.5 flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              Market Data
            </label>
            <div className="flex flex-wrap gap-1.5">
              {marketTags.map(tag => (
                <Badge
                  key={tag.id}
                  variant={selectedTags.has(tag.id) ? 'active' : 'outline'}
                  onClick={() => toggleTag(tag.id)}
                  className="text-xs"
                >
                  {tag.icon} {tag.label}
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs text-muted-foreground mb-1.5 flex items-center gap-1">
              <FileText className="h-3 w-3" />
              SEC Filings (10-K)
            </label>
            <div className="flex flex-wrap gap-1.5">
              {secTags.map(tag => (
                <Badge
                  key={tag.id}
                  variant={selectedTags.has(tag.id) ? 'active' : 'outline'}
                  onClick={() => toggleTag(tag.id)}
                  className="text-xs"
                >
                  {tag.icon} {tag.label}
                </Badge>
              ))}
            </div>
          </div>

          <Button onClick={generateQuery} className="w-full" size="sm">
            Generate Query →
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            📋 Quick Templates
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {quickTemplates.map((template, i) => (
            <Button
              key={i}
              variant="ghost"
              size="sm"
              className="w-full justify-start text-xs text-muted-foreground hover:text-foreground"
              onClick={() => onQueryGenerated(template.query)}
            >
              {template.label} for <span className="text-primary ml-1">{ticker}</span>
            </Button>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

