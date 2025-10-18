import React, { useEffect, useState } from 'react'
import { Button } from './ui/button'
import { useAuthToken, useAuthUser, useAuthActions } from '../stores/authStore'

export function AuthControls() {
  const token = useAuthToken()
  const user = useAuthUser()
  const { login, register, logout, fetchMe } = useAuthActions()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (token && !user) fetchMe().catch(() => {})
  }, [token, user, fetchMe])

  if (token) {
    return (
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <span style={{ opacity: 0.8 }}>
          Signed in as {user?.full_name || user?.email || 'user'}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => logout()}
          disabled={busy}
          aria-label="Logout"
        >
          Logout
        </Button>
      </div>
    )
  }

  return (
    <details>
      <summary>Auth</summary>
      <div style={{ display: 'grid', gridTemplateColumns: 'auto auto', gap: 8, paddingTop: 8 }}>
        <input
          placeholder="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value)
            setError(null)
          }}
        />
        <input
          placeholder="password"
          type="password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value)
            setError(null)
          }}
        />
        <input
          placeholder="username (opt)"
          value={username}
          onChange={(e) => {
            setUsername(e.target.value)
            setError(null)
          }}
        />
        <div style={{ display: 'flex', gap: 8 }}>
          <Button
            size="sm"
            onClick={async () => {
              setBusy(true)
              setError(null)
              try {
                const r = await login(email, password)
                if (!r.ok) setError(r.error || 'Login failed')
              } finally {
                setBusy(false)
              }
            }}
            disabled={busy || !email || !password}
            aria-label="Login"
          >
            Login
          </Button>
          <Button
            size="sm"
            onClick={async () => {
              setBusy(true)
              setError(null)
              try {
                const r = await register(email, password, username || undefined)
                if (!r.ok) setError(r.error || 'Register failed')
              } finally {
                setBusy(false)
              }
            }}
            disabled={busy || !email || !password}
            aria-label="Register"
          >
            Register
          </Button>
        </div>
        {error ? (
          <div style={{ gridColumn: '1 / -1', color: 'tomato', fontSize: 12 }}>{error}</div>
        ) : null}
      </div>
    </details>
  )
}
