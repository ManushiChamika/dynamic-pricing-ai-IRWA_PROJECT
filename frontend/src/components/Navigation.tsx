import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Button } from './ui/button'
import { Zap } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'

export function Navigation() {
  const navigate = useNavigate()
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()

  const isActive = (path: string) => location.pathname === path

  const linkClasses = (path: string) => {
    const base = 'text-base font-medium transition-colors'
    const active = theme === 'dark' ? 'text-indigo-300' : 'text-indigo-600'
    const inactive = theme === 'dark' ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'

    return `${base} ${isActive(path) ? active : inactive}`
  }

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 border-b backdrop-blur-lg transition-colors ${
        theme === 'dark' ? 'border-white/10 bg-[#0F172A]/80' : 'border-transparent bg-transparent'
      }`}
    >
      <div className="container mx-auto flex items-center gap-6 px-6 py-5">
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
          <span
            className={`text-2xl font-bold bg-gradient-to-r bg-clip-text text-transparent ${
              theme === 'dark' ? 'from-white to-gray-300' : 'from-gray-900 to-gray-600'
            }`}
          >
            FluxPricer
          </span>
        </div>

        <div className="flex flex-1 items-center justify-center">
          <div className="flex items-center gap-8">
            <span onClick={() => navigate('/')} className={`${linkClasses('/')} cursor-pointer`}>
              Home
            </span>
            <span onClick={() => navigate('/pricing')} className={`${linkClasses('/pricing')} cursor-pointer`}>
              Pricing
            </span>
            <span onClick={() => navigate('/contact')} className={`${linkClasses('/contact')} cursor-pointer`}>
              Contact Us
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span
            onClick={toggleTheme}
            className="cursor-pointer text-xl select-none"
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && toggleTheme()}
          >
            {theme === 'dark' ? '☾' : '☀'}
          </span>

          <Button
            variant="outline"
            onClick={() => navigate('/auth?mode=signin')}
            className={`${theme === 'dark' ? 'border-white/20 text-white hover:bg-white/10' : 'border-gray-300 text-gray-700 hover:bg-gray-50'}`}
          >
            Sign In
          </Button>
          <Button onClick={() => navigate('/auth?mode=signup')} className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white border-0">
            Get Started
          </Button>
        </div>
      </div>
    </nav>
  )
}