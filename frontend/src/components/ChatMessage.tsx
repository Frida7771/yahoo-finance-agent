import { cn } from '@/lib/utils'
import { User, Bot } from 'lucide-react'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === 'user'

  // Simple markdown-like formatting
  const formatContent = (text: string) => {
    return text
      .split('\n')
      .map((line) => {
        // Bold
        line = line.replace(/\*\*(.*?)\*\*/g, '<strong class="text-primary">$1</strong>')
        // Headers
        if (line.startsWith('### ')) {
          return `<h3 class="text-base font-semibold mt-4 mb-2">${line.slice(4)}</h3>`
        }
        if (line.startsWith('## ')) {
          return `<h2 class="text-lg font-semibold mt-4 mb-2">${line.slice(3)}</h2>`
        }
        // List items
        if (line.startsWith('- ')) {
          return `<li class="ml-4">${line.slice(2)}</li>`
        }
        // Table rows (simple)
        if (line.startsWith('|')) {
          return `<div class="font-mono text-xs bg-secondary/50 px-2 py-1 rounded">${line}</div>`
        }
        // Empty line
        if (!line.trim()) {
          return '<br/>'
        }
        return `<p>${line}</p>`
      })
      .join('')
  }

  return (
    <div className={cn(
      "flex gap-3",
      isUser && "flex-row-reverse"
    )}>
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center",
        isUser ? "bg-primary/10" : "bg-secondary"
      )}>
        {isUser ? (
          <User className="h-4 w-4 text-primary" />
        ) : (
          <Bot className="h-4 w-4 text-muted-foreground" />
        )}
      </div>
      
      <div className={cn(
        "max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed",
        isUser 
          ? "bg-primary/10 border border-primary/20" 
          : "bg-secondary"
      )}>
        <div 
          className="prose prose-invert prose-sm max-w-none"
          dangerouslySetInnerHTML={{ __html: formatContent(content) }}
        />
      </div>
    </div>
  )
}

export function LoadingMessage() {
  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-secondary flex items-center justify-center">
        <Bot className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="bg-secondary rounded-xl px-4 py-3">
        <div className="flex gap-1">
          <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  )
}

