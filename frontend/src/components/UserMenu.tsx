import { GoogleLogin } from '@react-oauth/google'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { LogOut, User } from 'lucide-react'

export function UserMenu() {
  const { user, isLoading, login, logout } = useAuth()

  if (isLoading) {
    return (
      <div className="h-10 w-10 rounded-full bg-secondary animate-pulse" />
    )
  }

  if (!user) {
    return (
      <GoogleLogin
        onSuccess={(credentialResponse) => {
          if (credentialResponse.credential) {
            login(credentialResponse.credential)
          }
        }}
        onError={() => {
          console.error('Google Login Failed')
        }}
        theme="filled_black"
        size="medium"
        shape="pill"
        text="signin"
      />
    )
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        {user.picture ? (
          <img 
            src={user.picture} 
            alt={user.name}
            className="h-8 w-8 rounded-full"
          />
        ) : (
          <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
            <User className="h-4 w-4 text-primary-foreground" />
          </div>
        )}
        <span className="text-sm font-medium hidden md:block">
          {user.name}
        </span>
      </div>
      <Button 
        variant="ghost" 
        size="icon"
        onClick={logout}
        title="Logout"
      >
        <LogOut className="h-4 w-4" />
      </Button>
    </div>
  )
}

