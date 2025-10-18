import { useSettings } from '../stores/settingsStore'
import { useToasts } from '../stores/toastStore'
import { triggerUnauthorized } from './apiClient'

export type SSEUpdateCallback = (update: {
  delta?: string
  thinking?: boolean
  agent?: string
  tool?: { name: string; status: 'running' | 'done' }
  turnStats?: {
    token_in?: number | null
    token_out?: number | null
    cost_usd?: string | number | null
    api_calls?: number | null
    model?: string | null
    provider?: string | null
    agents?: string[]
    tools?: string[]
  }
  threadRenamed?: { thread_id: number; title: string }
  done?: boolean
}) => void

export async function streamMessage(
  threadId: number,
  content: string,
  userName: string,
  onUpdate: SSEUpdateCallback,
  controller: AbortController
): Promise<void> {
  const token = localStorage.getItem('token') || ''
  const url = new URL(`/api/threads/${threadId}/messages/stream`, window.location.origin)
  if (token) url.searchParams.set('token', token)

  const decoder = new TextDecoder()
  let buf = ''
  let thinkingShown = false

  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ content, user_name: userName }),
      signal: controller.signal,
    })

    if (resp.status === 401) {
      try {
        triggerUnauthorized()
      } catch {
        /* ignore */
      }
      return
    } else if (!resp.ok) {
      useToasts.getState().push({ type: 'error', text: `Stream failed (${resp.status})` })
      return
    }

    const reader = resp.body?.getReader()
    if (!reader) return

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })

      let idx
      while ((idx = buf.indexOf('\n\n')) !== -1) {
        const frame = buf.slice(0, idx)
        buf = buf.slice(idx + 2)
        const lines = frame.split('\n').filter(Boolean)
        let ev: string | null = null
        let data: string | null = null

        for (const ln of lines) {
          if (ln.startsWith('event:')) ev = ln.split(':', 2)[1].trim()
          if (ln.startsWith('data:')) data = ln.slice(5).trim()
        }

        if (ev === 'thinking') {
          const s = useSettings.getState()
          if (s?.showThinking && !thinkingShown) {
            thinkingShown = true
            onUpdate({ thinking: true })
          }
          continue
        }

        if (ev === 'agent' && data) {
          try {
            const obj = JSON.parse(data)
            const name = obj.name || obj.agent || ''
            if (name) onUpdate({ agent: name })
          } catch {
            /* ignore */
          }
          continue
        }

        if (ev === 'tool_call' && data) {
          try {
            const obj = JSON.parse(data)
            const tool = obj.name || obj.tool || ''
            const status = obj.status || ''
            if (tool) {
              const toolStatus =
                status === 'start' ? 'running' : status === 'end' ? 'done' : 'running'
              onUpdate({ tool: { name: tool, status: toolStatus } })
            }
          } catch {
            /* ignore */
          }
          continue
        }

        if (ev === 'done') {
          onUpdate({ done: true })
          try {
            setTimeout(() => {
              onUpdate({ tool: undefined, agent: undefined })
            }, 1000)
          } catch {
            /* ignore */
          }
          return
        }

        if (ev === 'error') {
          try {
            if (data) {
              const obj = JSON.parse(data)
              const msg = obj.detail || obj.error || (typeof obj === 'string' ? obj : '')
              if (msg) useToasts.getState().push({ type: 'error', text: String(msg) })
            }
          } catch {
            /* ignore */
          }
          return
        }

        if (ev === 'message' && data) {
          try {
            const obj = JSON.parse(data)
            if (obj.delta) {
              onUpdate({ delta: obj.delta })
            } else if (obj.id) {
              const provider = obj?.metadata?.provider || null
              const agents = (obj?.agents?.activated || []) as string[]
              const tools = (obj?.tools?.used || []) as string[]
              onUpdate({
                turnStats: {
                  token_in: obj.token_in ?? null,
                  token_out: obj.token_out ?? null,
                  cost_usd: obj.cost_usd ?? null,
                  api_calls: obj.api_calls ?? null,
                  model: obj.model ?? null,
                  provider,
                  agents,
                  tools,
                },
              })
            }
          } catch {
            /* ignore */
          }
        }

        if (ev === 'thread_renamed' && data) {
          try {
            const obj = JSON.parse(data)
            if (obj.thread_id && obj.title) {
              onUpdate({ threadRenamed: { thread_id: obj.thread_id, title: obj.title } })
            }
          } catch {
            /* ignore */
          }
          continue
        }
      }
    }
  } catch {
    // AbortError or network error - ignore
  }
}
