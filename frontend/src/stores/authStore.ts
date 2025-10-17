import { create } from 'zustand'
import { api } from '../lib/apiClient'

export type AuthState = {
  token: string | null
  user: any | null
  setToken: (t: string | null) => void
  login: (email: string, password: string) => Promise<{ ok: boolean; error?: string }>
  register: (
    email: string,
    password: string,
    username?: string
  ) => Promise<{ ok: boolean; error?: string }>
  logout: () => Promise<void>
  fetchMe: () => Promise<{ ok: boolean; error?: string }>
}

export const useAuth = create<AuthState>((set, get) => ({
  token: localStorage.getItem('token'),
  user: null,
  setToken: (t) => {
    if (t) localStorage.setItem('token', t)
    else localStorage.removeItem('token')
    set({ token: t })
  },
  login: async (email, password) => {
    const res = await api('/api/login', { method: 'POST', json: { email, password } })
    if (res.ok && res.data?.token) {
      get().setToken(res.data.token)
      set({ user: res.data.user || null })
      return { ok: true }
    }
    const error =
      (res.data && (res.data.detail || res.data.error)) || `Login failed (${res.status})`
    return { ok: false, error }
  },
  register: async (email, password, username) => {
    const res = await api('/api/register', { method: 'POST', json: { email, password, username } })
    if (res.ok && res.data?.token) {
      get().setToken(res.data.token)
      set({ user: res.data.user || null })
      return { ok: true }
    }
    const error =
      (res.data && (res.data.detail || res.data.error)) || `Register failed (${res.status})`
    return { ok: false, error }
  },
  logout: async () => {
    const t = get().token
    if (t) await api('/api/logout', { method: 'POST', json: { token: t } })
    get().setToken(null)
    set({ user: null })
  },
  fetchMe: async () => {
    const t = get().token || localStorage.getItem('token')
    if (!t) return { ok: false, error: 'No token' }
    const res = await api('/api/me')
    if (res.ok && res.data?.user) {
      set({ user: res.data.user })
      return { ok: true }
    }
    const error =
      (res.data && (res.data.detail || res.data.error)) || `Auth check failed (${res.status})`
    return { ok: false, error }
  },
}))

export const useAuthToken = () => useAuth((state) => state.token)

export const useAuthUser = () => useAuth((state) => state.user)

export const useAuthActions = () =>
  useAuth((state) => ({
    login: state.login,
    register: state.register,
    logout: state.logout,
    fetchMe: state.fetchMe,
    setToken: state.setToken,
  }))
