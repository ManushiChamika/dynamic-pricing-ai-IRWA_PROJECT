import { create } from 'zustand'
import * as authApi from '../lib/authApi'

export interface User {
  email: string
  username?: string
  full_name?: string
  id?: string
}

export type AuthState = {
  token: string | null
  user: User | null
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
    const result = await authApi.login(email, password)
    if (result.ok && result.token) {
      get().setToken(result.token)
      set({ user: result.user || null })
      return { ok: true }
    }
    return { ok: false, error: result.error }
  },
  register: async (email, password, username) => {
    const result = await authApi.register(email, password, username)
    if (result.ok && result.token) {
      get().setToken(result.token)
      set({ user: result.user || null })
      return { ok: true }
    }
    return { ok: false, error: result.error }
  },
  logout: async () => {
    const t = get().token
    if (t) await authApi.logout(t)
    get().setToken(null)
    set({ user: null })
  },
  fetchMe: async () => {
    const t = get().token || localStorage.getItem('token')
    if (!t) return { ok: false, error: 'No token' }
    const result = await authApi.fetchMe()
    if (result.ok && result.user) {
      set({ user: result.user })
      return { ok: true }
    }
    return { ok: false, error: result.error }
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
