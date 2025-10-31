export type ApiResult<T = unknown> = { ok: boolean; status: number; data: T | null }

let unauthorizedHandler: (() => void) | null = null
export function setUnauthorizedHandler(fn: (() => void) | null) {
  unauthorizedHandler = fn
}

const MAX_RETRIES = 2
const RETRY_DELAY = 1000

async function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function fetchWithRetry(url: string, opts: RequestInit, retries = 0): Promise<Response> {
  try {
    const response = await fetch(url, opts)
    if (response.status >= 500 && retries < MAX_RETRIES && !opts.signal?.aborted) {
      await delay(RETRY_DELAY * (retries + 1))
      return fetchWithRetry(url, opts, retries + 1)
    }
    return response
  } catch (error: unknown) {
    if ((error as { name?: string })?.name === 'AbortError') {
      throw error
    }
    if (retries < MAX_RETRIES && !opts.signal?.aborted) {
      await delay(RETRY_DELAY * (retries + 1))
      return fetchWithRetry(url, opts, retries + 1)
    }
    throw error
  }
}

export async function api<T = unknown>(
  url: string,
  init?: RequestInit & { json?: unknown }
): Promise<ApiResult<T>> {
  const opts: RequestInit = {
    method: init?.method || 'GET',
    headers: init?.headers || {},
    signal: init?.signal,
  }
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

  const r = await fetchWithRetry(full, opts)
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
