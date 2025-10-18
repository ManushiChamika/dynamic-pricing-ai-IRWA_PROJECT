import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthToken } from '../stores/authStore'
import { useSettings } from '../stores/settingsStore'

export function ChatPage({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const token = useAuthToken()
  const { set: setSettings } = useSettings()

  useEffect(() => {
    const t = token ?? localStorage.getItem('token')
    if (!t) navigate('/auth')
  }, [token, navigate])

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'dark' | 'light' | null
    if (savedTheme) {
      setSettings({ theme: savedTheme })
    }
  }, [setSettings])

  return <>{children}</>
}
