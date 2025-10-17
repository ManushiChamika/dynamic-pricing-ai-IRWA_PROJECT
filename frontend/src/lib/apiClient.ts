export type ApiResult<T = any> = { ok: boolean; status: number; data: T | null }

let unauthorizedHandler: (() => void) | null = null
export function setUnauthorizedHandler(fn: (() => void) | null) {
  unauthorizedHandler = fn
}

// Centralized API helper that appends the token as a query param (backend expects this)
// and handles JSON body/response ergonomics.
export async function api<T = any>(
  url: string,
  init?: RequestInit & { json?: any }
): Promise<ApiResult<T>> {
  const opts: RequestInit = { method: init?.method || 'GET', headers: init?.headers || {} }
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') || '' : ''
  let full = url
  if (token && url.startsWith('/api/')) {
    const u = new URL(url, window.location.origin)
    if (!u.searchParams.get('token')) u.searchParams.set('token', token)
    full = u.pathname + u.search + u.hash
  }
  if (init?.json !== undefined) {
    opts.headers = { ...(opts.headers || {}), 'content-type': 'application/json' }
    opts.body = JSON.stringify(init.json)
  } else if (init?.body !== undefined) {
    opts.body = init.body
  }
  const r = await fetch(full, opts)
  const ct = r.headers.get('content-type') || ''
  const data = ct.includes('application/json') ? await r.json().catch(() => null) : null
  if (r.status === 401 && unauthorizedHandler) {
    try {
      unauthorizedHandler()
    } catch {
      /* ignore */
    }
  }
  return { ok: r.ok, status: r.status, data }
}

export function triggerUnauthorized() {
  if (unauthorizedHandler) {
    try {
      unauthorizedHandler()
    } catch {
      /* ignore */
    }
  }
}
