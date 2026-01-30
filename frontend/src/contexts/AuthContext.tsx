import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
  id: string
  email: string
  name: string
  picture?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (credential: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const TOKEN_KEY = 'quantbrains_token'
const USER_KEY = 'quantbrains_user'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Load user from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY)
    const savedUser = localStorage.getItem(USER_KEY)
    
    if (savedToken && savedUser) {
      setToken(savedToken)
      setUser(JSON.parse(savedUser))
      // Optionally verify token with backend
      verifyToken(savedToken)
    }
    setIsLoading(false)
  }, [])

  const verifyToken = async (token: string) => {
    try {
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
        localStorage.setItem(USER_KEY, JSON.stringify(userData))
      } else {
        // Token invalid, clear storage
        logout()
      }
    } catch (error) {
      console.error('Token verification failed:', error)
    }
  }

  const login = async (credential: string) => {
    setIsLoading(true)
    
    try {
      const response = await fetch('/api/auth/google', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ credential })
      })
      
      if (!response.ok) {
        throw new Error('Login failed')
      }
      
      const data = await response.json()
      
      // Save token and user
      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(data.user))
      setToken(data.access_token)
      setUser(data.user)
      
    } catch (error) {
      console.error('Login error:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

