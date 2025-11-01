import { Component, ReactNode, ErrorInfo } from 'react'
import { Button } from './ui/button'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex items-center justify-center min-h-screen bg-slate-950 text-white p-6">
          <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-lg p-8 text-center">
            <div className="flex justify-center mb-4">
              <div className="rounded-full bg-red-500/10 p-3">
                <AlertTriangle className="h-8 w-8 text-red-500" />
              </div>
            </div>
            <h2 className="text-xl font-bold mb-2">Something went wrong</h2>
            <p className="text-slate-400 mb-6">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <Button
              onClick={() => {
                this.setState({ hasError: false, error: null })
                window.location.reload()
              }}
              className="w-full"
            >
              Reload Page
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
