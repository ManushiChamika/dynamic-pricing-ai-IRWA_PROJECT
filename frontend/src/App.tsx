import { useEffect, useState, createContext, useContext } from 'react'
import { Link, Navigate, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function useAuth() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
  const [user, setUser] = useState<any | null>(null)

  useEffect(() => {
    if (!token) {
      setUser(null)
      return
    }
    fetch(`${API_BASE}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` }})
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => setUser(data.user))
      .catch(() => setUser(null))
  }, [token])

  const saveToken = (t: string | null) => {
    if (t) localStorage.setItem('token', t); else localStorage.removeItem('token')
    setToken(t)
  }
  return { token, user, setToken: saveToken }
}

function Protected({ children }: { children: React.ReactNode }) {
  const { token } = useAuthContext()
  const loc = useLocation()
  if (!token) return <Navigate to="/login" state={{ from: loc }} replace />
  return <>{children}</>
}

type AuthShape = ReturnType<typeof useAuth>
const AuthContext = createContext<AuthShape | undefined>(undefined)
function AuthProvider({ children }: { children: React.ReactNode }) {
  const auth = useAuth()
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>
}
function useAuthContext() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuthContext must be used within AuthProvider')
  return ctx
}

function Login() {
  const nav = useNavigate()
  const auth = useAuthContext()
  const [email, setEmail] = useState('demo@example.com')
  const [password, setPassword] = useState('demo1234')
  const [error, setError] = useState<string | null>(null)
  const loc = useLocation() as any
  const from = loc.state?.from?.pathname || '/'

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      const r = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      if (!r.ok) throw new Error((await r.json()).error || 'Login failed')
      const data = await r.json()
      auth.setToken(data.token)
      nav(from, { replace: true })
    } catch (err: any) { setError(err.message) }
  }
  return (
    <div style={{ maxWidth: 360, margin: '64px auto' }}>
      <h2>Login</h2>
      <form onSubmit={submit}>
        <input placeholder='email' value={email} onChange={e=>setEmail(e.target.value)} style={{ width:'100%', padding:8, marginBottom:8 }} />
        <input placeholder='password' type='password' value={password} onChange={e=>setPassword(e.target.value)} style={{ width:'100%', padding:8, marginBottom:8 }} />
        <button type='submit'>Sign in</button>
      </form>
      {error && <p style={{ color:'red' }}>{error}</p>}
      <p>New here? <Link to='/register'>Register</Link></p>
    </div>
  )
}

function Register() {
  const nav = useNavigate()
  const [email, setEmail] = useState('demo@example.com')
  const [password, setPassword] = useState('demo1234')
  const [name, setName] = useState('Demo User')
  const [msg, setMsg] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(null); setMsg(null)
    try {
      const r = await fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: name })
      })
      if (!r.ok) throw new Error((await r.json()).error || 'Registration failed')
      setMsg('Registered! You can now login')
      setTimeout(()=>nav('/login'), 500)
    } catch (err: any) { setError(err.message) }
  }
  return (
    <div style={{ maxWidth: 380, margin: '64px auto' }}>
      <h2>Register</h2>
      <form onSubmit={submit}>
        <input placeholder='full name' value={name} onChange={e=>setName(e.target.value)} style={{ width:'100%', padding:8, marginBottom:8 }} />
        <input placeholder='email' value={email} onChange={e=>setEmail(e.target.value)} style={{ width:'100%', padding:8, marginBottom:8 }} />
        <input placeholder='password' type='password' value={password} onChange={e=>setPassword(e.target.value)} style={{ width:'100%', padding:8, marginBottom:8 }} />
        <button type='submit'>Create account</button>
      </form>
      {msg && <p style={{ color:'green' }}>{msg}</p>}
      {error && <p style={{ color:'red' }}>{error}</p>}
      <p>Have an account? <Link to='/login'>Login</Link></p>
    </div>
  )
}

function Shell() {
  const nav = useNavigate()
  const auth = useAuthContext()
  const logout = async () => {
    if (!auth.token) return
    try { await fetch(`${API_BASE}/api/auth/logout`, { method:'POST', headers:{ Authorization:`Bearer ${auth.token}` }}) } catch {}
    auth.setToken(null)
    nav('/login')
  }
  return (
    <div style={{ padding: 16 }}>
      <header style={{ display:'flex', gap:12, alignItems:'center', marginBottom:16 }}>
        <h3 style={{ marginRight: 'auto' }}>IRWA Dynamic Pricing</h3>
        <Link to='/chat'>Chat</Link>
        <Link to='/analytics'>Analytics</Link>
        <button onClick={logout}>Logout</button>
      </header>
      <Outlet />
      <footer style={{ marginTop: 24, fontSize: 12, color: '#555' }}>
        Responsible AI: Decisions are suggestions; validate before applying.
      </footer>
    </div>
  )
}

function Chat() {
  const auth = useAuthContext()
  const [input, setInput] = useState('Show trending products')
  const [messages, setMessages] = useState<{ role:'user'|'assistant', text: string }[]>([])
  const send = async () => {
    const text = input.trim(); if (!text || !auth.token) return
    setMessages(m => [...m, { role: 'user', text }])
    setInput('')
    try {
      const r = await fetch(`${API_BASE}/api/chat`, { method:'POST', headers:{ 'Content-Type':'application/json', Authorization:`Bearer ${auth.token}` }, body: JSON.stringify({ message: text }) })
      const data = await r.json()
      const reply = data.reply || data.error || 'No response'
      setMessages(m => [...m, { role: 'assistant', text: reply }])
    } catch (e:any) {
      setMessages(m => [...m, { role: 'assistant', text: e.message }])
    }
  }
  return (
    <div>
      <div style={{ border:'1px solid #ddd', padding:12, minHeight:200, marginBottom:12 }}>
        {messages.length === 0 ? <p>Ask anything about prices, trends, pressure, stats…</p> : messages.map((m,i)=>(
          <div key={i} style={{ marginBottom: 8 }}>
            <b>{m.role === 'user' ? 'You' : 'Assistant'}:</b> {m.text}
          </div>
        ))}
      </div>
      <div style={{ display:'flex', gap:8 }}>
        <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=> e.key==='Enter' && send()} style={{ flex:1, padding:8 }} />
        <button onClick={send}>Send</button>
      </div>
    </div>
  )
}

function Analytics() {
  const [trending, setTrending] = useState<any[]>([])
  const [movers, setMovers] = useState<any[]>([])
  const [pressure, setPressure] = useState<any[]>([])
  useEffect(() => {
    const load = async () => {
      const t = await fetch(`${API_BASE}/api/analytics/trending`).then(r=>r.json()).catch(()=>({ items: [] }))
      const m = await fetch(`${API_BASE}/api/analytics/movers`).then(r=>r.json()).catch(()=>({ items: [] }))
      const p = await fetch(`${API_BASE}/api/analytics/pressure`).then(r=>r.json()).catch(()=>({ items: [] }))
      setTrending(t.items || []); setMovers(m.items || []); setPressure(p.items || [])
    }
    load()
  }, [])
  return (
    <div style={{ display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:12 }}>
      <div>
        <h4>Trending by Volume</h4>
        <ul>{trending.map((x,i)=>(<li key={i}>{JSON.stringify(x)}</li>))}</ul>
      </div>
      <div>
        <h4>Top Price Movers</h4>
        <ul>{movers.map((x,i)=>(<li key={i}>{JSON.stringify(x)}</li>))}</ul>
      </div>
      <div>
        <h4>Competitor Pressure</h4>
        <ul>{pressure.map((x,i)=>(<li key={i}>{JSON.stringify(x)}</li>))}</ul>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<Protected><Shell /></Protected>}>
          <Route index element={<Navigate to="/chat" replace />} />
          <Route path="chat" element={<Chat />} />
          <Route path="analytics" element={<Analytics />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
