import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { API_URL } from '../config'

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const MIN_PASSWORD = 10

export default function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
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
      const trimmedUsername = username.trim()

      if (!trimmedUsername) {
        setError('Please enter your name.')
        return
      }

      if (!trimmedEmail || !emailRegex.test(trimmedEmail)) {
        setError('Please enter a valid email address.')
        return
      }

      if (!trimmedPassword || trimmedPassword.length < MIN_PASSWORD) {
        setError(`Password must be at least ${MIN_PASSWORD} characters.`)
        return
      }

      setIsSubmitting(true)
      try {
        const res = await fetch(`${API_URL}/api/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: trimmedEmail, password: trimmedPassword, username: trimmedUsername })
        })
        const data = await res.json()
        if (!res.ok || !data?.ok) throw new Error(data?.detail || 'Registration failed')

        // Do NOT auto-login. Send user back to landing to login explicitly.
        setSuccess('✅ Registration successful! Please log in to continue.')
        setTimeout(() => {
          window.location.href = '/'
        }, 1200)
      } catch (err) {
        setError(err.message || 'Registration failed')
      }
      setIsSubmitting(false)
    })()
  }

  return (
    <div className="container" style={{ maxWidth: 480 }}>
      <h1 style={{ color: '#2563eb' }}>Register</h1>
  <p className="subtitle">Create your account.</p>
  {success && <div style={{ color: '#16a34a', marginTop: 8 }}>{success}</div>}
      {error && <div style={{ color: '#dc2626', marginTop: 8 }}>{error}</div>}
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12, marginTop: 16 }}>
        <label>
          <div style={{ fontWeight: 600 }}>Username</div>
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="your name" type="text" required style={{ width: '100%', padding: 10, borderRadius: 8, border: '1px solid #cbd5e1' }} />
        </label>
        <label>
          <div style={{ fontWeight: 600 }}>Email</div>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" type="email" required style={{ width: '100%', padding: 10, borderRadius: 8, border: '1px solid #cbd5e1' }} />
        </label>
        <label>
          <div style={{ fontWeight: 600 }}>Password</div>
          <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" type="password" required minLength={MIN_PASSWORD} style={{ width: '100%', padding: 10, borderRadius: 8, border: '1px solid #cbd5e1' }} />
        </label>
        <div className="actions" style={{ justifyContent: 'flex-start' }}>
          <button className="btn primary" type="submit" disabled={isSubmitting}>{isSubmitting ? 'Submitting…' : 'Continue'}</button>
          <Link className="btn" to="/">← Back</Link>
        </div>
      </form>
    </div>
  )
}
