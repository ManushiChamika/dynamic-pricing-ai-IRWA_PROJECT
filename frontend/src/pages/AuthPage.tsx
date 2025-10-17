import { useState, FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { Navigation } from '../components/Navigation'
import { useAuth } from '../stores/authStore'
import { useTheme } from '../contexts/ThemeContext'

export function AuthPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const pageBackground = isDark
    ? 'bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900'
    : 'bg-gradient-to-b from-slate-50 via-slate-100 to-slate-50'
  const headingColor = isDark ? 'text-white' : 'text-slate-900'
  const helperText = isDark ? 'text-gray-400' : 'text-slate-700'
  const cardSurface = isDark
    ? 'bg-gray-800/50 border-gray-700'
    : 'bg-white/95 border-slate-200 shadow-[0_20px_45px_rgba(15,23,42,0.12)]'
  const labelColor = isDark ? 'text-gray-300' : 'text-slate-700'
  const inputClass = isDark
    ? 'bg-gray-900 border-gray-600 text-white'
    : 'bg-white border-slate-300 text-slate-900 shadow-sm'
  const switchLink = isDark
    ? 'text-indigo-300 hover:text-indigo-200'
    : 'text-indigo-600 hover:text-indigo-700'
  const backLink = isDark
    ? 'text-gray-400 hover:text-gray-300'
    : 'text-slate-600 hover:text-slate-700'
  const [mode, setMode] = useState<'signin' | 'signup'>(
    searchParams.get('mode') === 'signup' ? 'signup' : 'signin'
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')

  const auth = useAuth()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      let result
      if (mode === 'signin') {
        result = await auth.login(email, password)
      } else {
        result = await auth.register(email, password, username)
      }
      if (!result.ok) {
        throw new Error(result.error || 'Authentication failed')
      }
      navigate('/chat')
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`min-h-screen ${pageBackground}`}>
      <Navigation />
      <div className="flex items-center justify-center px-4 pt-24 pb-12 min-h-screen">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <div className="flex items-center justify-center gap-2 mb-4">
              <svg
                className="h-10 w-10 text-indigo-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              <span className={`text-2xl font-bold ${headingColor}`}>FluxPricer</span>
            </div>
            <h1 className={`text-3xl font-bold ${headingColor}`}>
              {mode === 'signin' ? 'Welcome Back' : 'Create Account'}
            </h1>
            <p className={`mt-2 ${helperText}`}>
              {mode === 'signin'
                ? 'Sign in to access your pricing dashboard'
                : 'Start optimizing your pricing with AI'}
            </p>
          </div>

          <div className={`${cardSurface} backdrop-blur-sm border rounded-lg p-8`}>
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'signup' && (
                <div>
                  <label
                    htmlFor="username"
                    className={`block text-sm font-medium ${labelColor} mb-2`}
                  >
                    Full Name
                  </label>
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className={`w-full px-4 py-2 ${inputClass} border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500`}
                    placeholder="John Doe"
                  />
                </div>
              )}

              <div>
                <label htmlFor="email" className={`block text-sm font-medium ${labelColor} mb-2`}>
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className={`w-full px-4 py-2 ${inputClass} border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500`}
                  placeholder="you@example.com"
                />
              </div>

              <div>
                <label
                  htmlFor="password"
                  className={`block text-sm font-medium ${labelColor} mb-2`}
                >
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className={`w-full px-4 py-2 ${inputClass} border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500`}
                  placeholder="••••••••"
                />
              </div>

              {error && (
                <div
                  className={`${theme === 'dark' ? 'bg-red-500/10 border-red-500 text-red-500' : 'bg-red-50 border-red-300 text-red-700'} border px-4 py-2 rounded-md text-sm`}
                >
                  {error}
                </div>
              )}

              <Button type="submit" disabled={loading} className="w-full h-11">
                {loading ? 'Processing...' : mode === 'signin' ? 'Sign In' : 'Create Account'}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <button
                type="button"
                onClick={() => {
                  setMode(mode === 'signin' ? 'signup' : 'signin')
                  setError('')
                }}
                className={`text-sm ${switchLink}`}
              >
                {mode === 'signin'
                  ? "Don't have an account? Sign up"
                  : 'Already have an account? Sign in'}
              </button>
            </div>

            <div className="mt-4 text-center">
              <button type="button" onClick={() => navigate('/')} className={`text-sm ${backLink}`}>
                ← Back to home
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
