import React, { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Button } from './ui/button'
import { Zap } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'
import { useAuthUser, useAuthActions, useAuthToken } from '../stores/authStore'

export function Navigation() {
  const navigate = useNavigate()
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'
  const user = useAuthUser()
  const token = useAuthToken()
  const { logout, fetchMe } = useAuthActions()

  useEffect(() => {
    if (token && !user) {
      fetchMe()
    }
  }, [token, user, fetchMe])

  const isActive = (path: string) => location.pathname === path

  const linkClasses = (path: string) => {
    const base = 'text-base font-medium transition-colors'
    const active = isDark ? 'text-indigo-300' : 'text-indigo-700'
    const inactive = isDark
      ? 'text-gray-300 hover:text-white'
      : 'text-slate-700 hover:text-slate-900'

    return `${base} ${isActive(path) ? active : inactive}`
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex items-center gap-6 px-6 py-4">
        <div
          className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
          onClick={() => navigate('/')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/')}
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
            <Zap className="h-6 w-6 text-white fill-white" />
          </div>
          <span className="text-2xl font-bold">FluxPricer</span>
        </div>

        <div className="flex flex-1 items-center justify-center">
          <div className="flex items-center gap-8">
            <span onClick={() => navigate('/')} className={`${linkClasses('/')} cursor-pointer`}>
              Home
            </span>
            <span
              onClick={() => navigate('/pricing')}
              className={`${linkClasses('/pricing')} cursor-pointer`}
            >
              Pricing
            </span>
            <span
              onClick={() => navigate('/contact')}
              className={`${linkClasses('/contact')} cursor-pointer`}
            >
              Contact Us
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDark ? '☾' : '☀'}
          </Button>

          {user ? (
            <>
              <span className="text-sm font-medium text-muted-foreground">
                {user.full_name || user.email}
              </span>
              <Button
                variant="outline"
                onClick={async () => {
                  try {
                    await logout()
                  } catch {
                    /* ignore */
                  }
                  window.location.href = '/'
                }}
              >
                Logout
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={() => navigate('/auth?mode=signin')}>
                Sign In
              </Button>
              <Button onClick={() => navigate('/auth?mode=signup')}>Get Started</Button>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
