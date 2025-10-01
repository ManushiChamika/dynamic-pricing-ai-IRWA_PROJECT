import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export function ChatPage({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      navigate('/auth')
    }
  }, [navigate])

  return <>{children}</>
}
