import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthToken } from '../stores/authStore'

export function ChatPage({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const token = useAuthToken()

  useEffect(() => {
    const t = token ?? localStorage.getItem('token')
    if (!t) navigate('/auth')
  }, [token, navigate])

  return <>{children}</>
}
