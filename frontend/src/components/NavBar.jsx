import React, { useEffect, useMemo, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { API_URL, STREAMLIT_URL } from '../config'

const COOKIE_NAME = 'fp_session'

const getCookie = (name) => {
  if (typeof document === 'undefined') return null
  const parts = document.cookie.split(';').map((p) => p.trim())
  const match = parts.find((part) => part.startsWith(`${name}=`))
  return match ? decodeURIComponent(match.split('=')[1]) : null
}

const clearSessionCookie = () => {
  if (typeof document === 'undefined') return
  document.cookie = `${COOKIE_NAME}=; Path=/; Max-Age=0; SameSite=Lax`
  document.cookie = `${COOKIE_NAME}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`
}

export default function NavBar() {
  const navigate = useNavigate()
  const [session, setSession] = useState(null)
  const [isLoadingSession, setIsLoadingSession] = useState(true)
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  useEffect(() => {
    let cancelled = false
    const token = getCookie(COOKIE_NAME)
    if (!token) {
      setSession(null)
      setIsLoadingSession(false)
      return
    }
    (async () => {
      try {
        const res = await fetch(`${API_URL}/api/me?token=${encodeURIComponent(token)}`, {
          credentials: 'include'
        })
        if (!res.ok) throw new Error('Session invalid')
        const data = await res.json()
        if (!data?.ok || !data?.user) throw new Error('Invalid session response')
        if (!cancelled) {
          setSession({ user: data.user, token })
        }
      } catch (err) {
        clearSessionCookie()
        if (!cancelled) {
          setSession(null)
        }
      } finally {
        if (!cancelled) {
          setIsLoadingSession(false)
        }
      }
    })()

    return () => {
      cancelled = true
    }
  }, [])

  const handleLogout = async () => {
    if (isLoggingOut) return
    setIsLoggingOut(true)
    const token = session?.token || getCookie(COOKIE_NAME)
    try {
      if (token) {
        await fetch(`${API_URL}/api/logout`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token }),
          credentials: 'include'
        })
      }
    } catch (err) {
      // Best-effort logout; ignore network errors but clear client state
    } finally {
      clearSessionCookie()
      setSession(null)
      setIsLoggingOut(false)
      navigate('/')
    }
  }

  const userInitials = useMemo(() => {
    const fullName = session?.user?.full_name || ''
    if (!fullName) return null
    return fullName
      .split(' ')
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join('')
  }, [session])

  return (
    <header className="navbar">
      <div className="nav-inner">
        <div className="brand">
          <Link to="/" className="brand-link">FluxPricer AI</Link>
        </div>
        <nav className="nav-links">
          <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Home</NavLink>
          <NavLink to="/pricing" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Pricing</NavLink>
        </nav>
        <div className="nav-actions">
          {isLoadingSession ? (
            <span className="nav-status">Checking session…</span>
          ) : session ? (
            <>
              <a href={`${STREAMLIT_URL}/?page=dashboard`} className="btn small secondary">Dashboard</a>
              <button className="btn small" onClick={handleLogout} disabled={isLoggingOut}>
                {isLoggingOut ? 'Logging out…' : 'Logout'}
              </button>
              {session.user?.email && (
                <span className="user-pill" title={session.user.email}>
                  {userInitials || session.user.email.split('@')[0]}
                </span>
              )}
            </>
          ) : (
            <>
              <Link to="/login" className="btn small">Login</Link>
              <Link to="/register" className="btn small primary">Register</Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
