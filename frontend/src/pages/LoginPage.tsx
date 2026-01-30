import { GoogleLogin } from '@react-oauth/google'
import { useAuth } from '@/contexts/AuthContext'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, BarChart3, FileText, Zap, Shield, LineChart } from 'lucide-react'

export function LoginPage() {
  const { login, isLoading } = useAuth()

  const features = [
    { icon: TrendingUp, label: 'Real-time Stock Data', color: 'text-green-500' },
    { icon: BarChart3, label: 'Financial Analysis', color: 'text-blue-500' },
    { icon: FileText, label: 'SEC 10-K Reports', color: 'text-purple-500' },
    { icon: LineChart, label: 'Live Market Dashboard', color: 'text-cyan-500' },
    { icon: Shield, label: 'AI Risk Assessment', color: 'text-orange-500' },
    { icon: Zap, label: 'Powered by LangChain', color: 'text-yellow-500' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/10 flex items-center justify-center p-6">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5 pointer-events-none" />
      
      <div className="w-full max-w-5xl grid md:grid-cols-2 gap-8 items-center relative z-10">
        {/* Left Side - Branding */}
        <div className="space-y-8">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-5xl">📈</span>
              <div>
                <h1 className="text-4xl font-bold">QuantBrains</h1>
                <p className="text-muted-foreground">AI-Powered Financial Analysis</p>
              </div>
            </div>
            
            <p className="text-lg text-muted-foreground leading-relaxed">
              Your intelligent assistant for stock analysis, SEC filings research, 
              and real-time market monitoring — all through natural language.
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-2 gap-3">
            {features.map((feature) => (
              <div 
                key={feature.label}
                className="flex items-center gap-2 p-3 rounded-lg bg-secondary/50"
              >
                <feature.icon className={`h-5 w-5 ${feature.color}`} />
                <span className="text-sm">{feature.label}</span>
              </div>
            ))}
          </div>

          {/* Tech Badges */}
          <div className="flex flex-wrap gap-2">
            {['LangChain', 'GPT-4', 'Yahoo Finance', 'SEC EDGAR', 'Redis'].map(tech => (
              <Badge key={tech} variant="outline" className="text-xs">
                {tech}
              </Badge>
            ))}
          </div>
        </div>

        {/* Right Side - Login Card */}
        <Card className="shadow-2xl shadow-primary/10 border-primary/20">
          <CardContent className="p-8 space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-semibold">Welcome</h2>
              <p className="text-muted-foreground">
                Sign in to access your personalized financial dashboard
              </p>
            </div>

            {/* Google Login Button */}
            <div className="flex justify-center py-4">
              {isLoading ? (
                <div className="h-10 w-full max-w-[240px] bg-secondary rounded-full animate-pulse" />
              ) : (
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
                  size="large"
                  shape="pill"
                  width="240"
                  text="continue_with"
                />
              )}
            </div>

          </CardContent>
        </Card>
      </div>

      {/* Footer */}
      <footer className="absolute bottom-4 text-center text-xs text-muted-foreground">
        © 2025 QuantBrains • Built with FastAPI, React & LangChain
      </footer>
    </div>
  )
}

