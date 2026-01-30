import { useState, useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import { Zap, Crown } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

interface UsageData {
  is_premium: boolean
  used: number
  limit: number
  remaining: number
  reset_at: string | null
}

export function UsageQuota() {
  const { token } = useAuth()
  const [usage, setUsage] = useState<UsageData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      fetchUsage()
    }
  }, [token])

  const fetchUsage = async () => {
    try {
      const res = await fetch('/api/chat/usage', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setUsage(data)
      }
    } catch (error) {
      console.error('Failed to fetch usage:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading || !usage) {
    return null
  }

  // 付费用户
  if (usage.is_premium) {
    return (
      <Badge variant="default" className="bg-gradient-to-r from-yellow-500 to-orange-500 text-white gap-1">
        <Crown className="h-3 w-3" />
        Premium
      </Badge>
    )
  }

  // 免费用户
  const hasQuota = usage.remaining > 0

  return (
    <Badge 
      variant={hasQuota ? "secondary" : "destructive"} 
      className={`gap-1 ${hasQuota ? '' : 'bg-red-500/20 text-red-500 border-red-500/50'}`}
    >
      <Zap className="h-3 w-3" />
      {hasQuota 
        ? `${usage.remaining} free analysis left`
        : 'No free analysis left'
      }
    </Badge>
  )
}

// Hook 版本，供其他组件使用
export function useUsageQuota() {
  const { token } = useAuth()
  const [usage, setUsage] = useState<UsageData | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchUsage = async () => {
    if (!token) return
    try {
      const res = await fetch('/api/chat/usage', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setUsage(data)
      }
    } catch (error) {
      console.error('Failed to fetch usage:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsage()
  }, [token])

  return { usage, loading, refetch: fetchUsage }
}

