import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { QueryBuilder } from './QueryBuilder'
import { Plus, MessageSquare, TrendingUp, Home } from 'lucide-react'

interface Conversation {
  id: string
  title: string
}

interface SidebarProps {
  conversations: Conversation[]
  currentConversationId: string | null
  onNewChat: () => void
  onSelectConversation: (id: string) => void
  onQueryGenerated: (query: string) => void
  onNavigateToHome?: () => void
}

export function Sidebar({
  conversations,
  currentConversationId,
  onNewChat,
  onSelectConversation,
  onQueryGenerated,
  onNavigateToHome,
}: SidebarProps) {
  return (
    <div className="w-80 border-r bg-card flex flex-col h-screen">
      {/* Logo */}
      <div className="p-4 border-b flex items-center justify-between">
        <h1 className="text-lg font-semibold text-primary flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          AI Analysis
        </h1>
        {onNavigateToHome && (
          <Button variant="ghost" size="icon" onClick={onNavigateToHome} title="Back to Home">
            <Home className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <Button onClick={onNewChat} variant="outline" className="w-full justify-start gap-2">
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      {/* Query Builder */}
      <div className="px-4 pb-4">
        <QueryBuilder onQueryGenerated={onQueryGenerated} />
      </div>

      {/* Conversations List */}
      <div className="px-4 pb-2">
        <h3 className="text-xs text-muted-foreground font-medium">Recent Chats</h3>
      </div>
      
      <ScrollArea className="flex-1 px-4">
        <div className="space-y-1 pb-4">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => onSelectConversation(conv.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors truncate flex items-center gap-2 ${
                conv.id === currentConversationId
                  ? 'bg-secondary text-foreground'
                  : 'text-muted-foreground hover:bg-secondary/50 hover:text-foreground'
              }`}
            >
              <MessageSquare className="h-3 w-3 flex-shrink-0" />
              {conv.title || 'New Chat'}
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
