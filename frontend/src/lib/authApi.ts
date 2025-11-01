import { api } from './apiClient'

export interface User {
  email: string
  username?: string
  full_name?: string
  id?: string
}

export type AuthResponse = { ok: boolean; error?: string }

export type LoginSuccess = { token: string; user?: User | null }
export type ErrorResponse = { detail?: string; error?: string }

function isErrorResponse(d: unknown): d is ErrorResponse {
  return !!d && typeof d === 'object' && ('detail' in (d as any) || 'error' in (d as any))
}

export type LoginResult = {
  ok: boolean
  token?: string
  user?: User | null
  error?: string
}

export async function login(email: string, password: string): Promise<LoginResult> {
  const res = await api<LoginSuccess | ErrorResponse>('/api/login', {
    method: 'POST',
    json: { email, password },
  })
  if (res.ok && res.data && 'token' in res.data) {
    return { ok: true, token: res.data.token, user: res.data.user ?? null }
  }
  const error = isErrorResponse(res.data)
    ? res.data.detail ?? res.data.error
    : `Login failed (${res.status})`
  return { ok: false, error }
}

export async function register(
  email: string,
  password: string,
  username?: string
): Promise<LoginResult> {
  const res = await api<LoginSuccess | ErrorResponse>('/api/register', {
    method: 'POST',
    json: { email, password, username },
  })
  if (res.ok && res.data && 'token' in res.data) {
    return { ok: true, token: res.data.token, user: res.data.user ?? null }
  }
  const error = isErrorResponse(res.data)
    ? res.data.detail ?? res.data.error
    : `Register failed (${res.status})`
  return { ok: false, error }
}

export async function logout(token: string): Promise<void> {
  await api('/api/logout', { method: 'POST', json: { token } })
}

type MeResponse = { user: User }

export async function fetchMe(): Promise<{ ok: boolean; user?: User; error?: string }> {
  const res = await api<MeResponse | ErrorResponse>('/api/me')
  if (res.ok && res.data && 'user' in res.data) {
    return { ok: true, user: res.data.user }
  }
  const error = isErrorResponse(res.data)
    ? res.data.detail ?? res.data.error
    : `Auth check failed (${res.status})`
  return { ok: false, error }
}
