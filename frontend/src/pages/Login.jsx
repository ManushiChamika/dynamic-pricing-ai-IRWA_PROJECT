import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { STREAMLIT_URL, API_URL } from '../config'

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    ;(async () => {
      if (isSubmitting) return
      setError('')
      setSuccess('')

      const trimmedEmail = email.trim().toLowerCase()
      const trimmedPassword = password.trim()

      if (!trimmedEmail || !emailRegex.test(trimmedEmail)) {
        setError('Please enter a valid email address.')
        return
      }

      if (!trimmedPassword) {
        setError('Password is required.')
        return
      }

      setIsSubmitting(true)
      try {
        const res = await fetch(`${API_URL}/api/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: trimmedEmail, password: trimmedPassword })
        })
        const data = await res.json()
        if (!res.ok || !data?.ok) throw new Error(data?.detail || 'Login failed')

        const expires = new Date(data.expires_at)
        document.cookie = `fp_session=${data.token}; Path=/; SameSite=Lax; Expires=${expires.toUTCString()}`

        const meRes = await fetch(`${API_URL}/api/me?token=${encodeURIComponent(data.token)}`)
        const me = await meRes.json()
        if (!meRes.ok || !me?.ok) throw new Error('Verification failed')

        setSuccess('✅ Login successful! Redirecting to dashboard...')
        setTimeout(() => {
          window.location.href = `${STREAMLIT_URL}/?page=dashboard`
        }, 800)
      } catch (err) {
        setError(err.message || 'Login failed')
      }
      setIsSubmitting(false)
    })()
  }

  return (
    <div className="container" style={{ maxWidth: 480 }}>
      <h1 style={{ color: '#2563eb' }}>Login</h1>
  <p className="subtitle">Sign in to your account.</p>
  {success && <div style={{ color: '#16a34a', marginTop: 8 }}>{success}</div>}
  {error && <div style={{ color: '#dc2626', marginTop: 8 }}>{error}</div>}

      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12, marginTop: 16 }}>
        <label>
          <div style={{ fontWeight: 600 }}>Email</div>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" type="email" required style={{ width: '100%', padding: 10, borderRadius: 8, border: '1px solid #cbd5e1' }} />
        </label>
        <label>
          <div style={{ fontWeight: 600 }}>Password</div>
          <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" type="password" required style={{ width: '100%', padding: 10, borderRadius: 8, border: '1px solid #cbd5e1' }} />
        </label>
        <div className="actions" style={{ justifyContent: 'flex-start' }}>
          <button className="btn primary" type="submit" disabled={isSubmitting}>{isSubmitting ? 'Signing in…' : 'Continue'}</button>
          <Link className="btn" to="/">← Back</Link>
        </div>
      </form>
    </div>
  )
}
