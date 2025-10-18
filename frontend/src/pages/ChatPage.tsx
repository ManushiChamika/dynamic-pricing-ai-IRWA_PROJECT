import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../stores/authStore'

export function ChatPage({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const { token, user, fetchMe } = useAuth()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      const t = token ?? localStorage.getItem('token')
      if (!t) {
        navigate('/auth')
        return
      }
      if (!user) {
        const { ok } = await fetchMe()
        if (!ok) {
          navigate('/auth')
        }
      }
      setLoading(false)
    }
    checkAuth()
  }, [token, user, fetchMe, navigate])

  if (loading) {
    return <div className="loading">Authenticating…</div>
  }

  return <>{children}</>
}
