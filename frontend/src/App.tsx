import { useState, useRef, useEffect } from 'react'
import { Sidebar } from '@/components/Sidebar'
import { ChatMessage, LoadingMessage } from '@/components/ChatMessage'
import { HomePage } from '@/pages/HomePage'
import { QuotesPage } from '@/pages/QuotesPage'
import { LoginPage } from '@/pages/LoginPage'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Card, CardContent } from '@/components/ui/card'
import { Send, TrendingUp, BarChart3, FileText, Home } from 'lucide-react'
import { UserMenu } from '@/components/UserMenu'
import { useAuth } from '@/contexts/AuthContext'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Conversation {
  id: string
  title: string
  messages?: Message[]
}

type Page = 'home' | 'analysis' | 'quotes'

// Get initial page from URL hash
function getPageFromHash(): Page {
  const hash = window.location.hash.slice(1) // Remove #
  if (hash === 'analysis' || hash === 'quotes') {
    return hash
  }
  return 'home'
}

function App() {
  const { user, isLoading: authLoading } = useAuth()
  const [currentPage, setCurrentPage] = useState<Page>(getPageFromHash)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Sync URL hash with current page
  useEffect(() => {
    window.location.hash = currentPage === 'home' ? '' : currentPage
  }, [currentPage])

  // Handle browser back/forward buttons
  useEffect(() => {
    const handleHashChange = () => {
      setCurrentPage(getPageFromHash())
    }
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  // Load conversations on mount
  useEffect(() => {
    loadConversations()
  }, [])

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

  const loadConversations = async () => {
    try {
      const res = await fetch('/api/chat/conversations')
      const data = await res.json()
      setConversations(data.slice(0, 10))
    } catch (error) {
      console.error('Failed to load conversations:', error)
    }
  }

  const loadConversation = async (id: string) => {
    try {
      const res = await fetch(`/api/chat/conversations/${id}`)
      const data = await res.json()
      setCurrentConversationId(id)
      setMessages(data.messages || [])
    } catch (error) {
      console.error('Failed to load conversation:', error)
    }
  }

  const newChat = () => {
    setCurrentConversationId(null)
    setMessages([])
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: currentConversationId,
        }),
      })

      const data = await res.json()

      if (res.ok) {
        setCurrentConversationId(data.conversation_id)
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
        loadConversations()
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${data.detail || 'Something went wrong'}` }])
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${error}` }])
    }

    setIsLoading(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleQueryGenerated = (query: string) => {
    setInput(query)
    textareaRef.current?.focus()
  }

  const navigateToAnalysis = (prefilledQuery?: string) => {
    if (prefilledQuery) {
      setInput(prefilledQuery)
    }
    setCurrentPage('analysis')
  }

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse text-2xl">📈 Loading...</div>
      </div>
    )
  }

  // Show login page if not authenticated
  if (!user) {
    return <LoginPage />
  }

  // Render Home Page
  if (currentPage === 'home') {
    return (
      <HomePage 
        onNavigateToAnalysis={navigateToAnalysis}
        onNavigateToQuotes={() => setCurrentPage('quotes')}
      />
    )
  }

  // Render Quotes Page
  if (currentPage === 'quotes') {
    return <QuotesPage onBack={() => setCurrentPage('home')} />
  }

  // Render Analysis Page (Chat)
  return (
    <div className="flex h-screen bg-background">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onNewChat={newChat}
        onSelectConversation={loadConversation}
        onQueryGenerated={handleQueryGenerated}
        onNavigateToHome={() => setCurrentPage('home')}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Header - Same style as Dashboard */}
        <header className="border-b px-6 py-4 flex-shrink-0 flex items-center justify-between">
          <h1 className="text-xl font-semibold flex items-center gap-2">
            🤖 AI Analysis
          </h1>
          <div className="flex items-center gap-4">
            <UserMenu />
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setCurrentPage('home')}
              className="gap-2"
            >
              <Home className="h-4 w-4" />
              Home
            </Button>
          </div>
        </header>

        {/* Messages */}
        <ScrollArea className="flex-1">
          <div className="p-6 space-y-6">
            {messages.length === 0 ? (
              <WelcomeScreen />
            ) : (
              <>
                {messages.map((msg, i) => (
                  <ChatMessage key={i} role={msg.role} content={msg.content} />
                ))}
                {isLoading && <LoadingMessage />}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t p-4 flex-shrink-0 bg-card">
          <div className="flex gap-3 max-w-4xl mx-auto">
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about any stock... e.g. 'Analyze NVDA's valuation and risks'"
                className="w-full bg-secondary border border-border rounded-xl px-4 py-3 pr-12 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-ring min-h-[48px] max-h-[200px]"
                rows={1}
              />
            </div>
            <Button
              onClick={sendMessage}
              disabled={isLoading || !input.trim()}
              size="icon"
              className="h-12 w-12 rounded-xl"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

function WelcomeScreen() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h1 className="text-3xl font-bold text-primary mb-3">📈 AI Analysis</h1>
      <p className="text-muted-foreground mb-8 max-w-md">
        Ask questions about any stock. Get real-time data, financials, and SEC filings analysis.
      </p>

      <div className="grid grid-cols-3 gap-4 max-w-2xl">
        <Card className="text-left">
          <CardContent className="pt-6">
            <TrendingUp className="h-6 w-6 text-primary mb-2" />
            <h3 className="font-medium mb-1">Stock Data</h3>
            <p className="text-xs text-muted-foreground">
              Real-time prices, historical data, and market metrics
            </p>
          </CardContent>
        </Card>

        <Card className="text-left">
          <CardContent className="pt-6">
            <BarChart3 className="h-6 w-6 text-green-500 mb-2" />
            <h3 className="font-medium mb-1">Financials</h3>
            <p className="text-xs text-muted-foreground">
              Revenue, profit, ROE, valuation ratios
            </p>
          </CardContent>
        </Card>

        <Card className="text-left">
          <CardContent className="pt-6">
            <FileText className="h-6 w-6 text-purple-500 mb-2" />
            <h3 className="font-medium mb-1">SEC 10-K</h3>
            <p className="text-xs text-muted-foreground">
              Risks, Legal, Executives, Compensation
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default App
