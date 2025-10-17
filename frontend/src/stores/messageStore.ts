import { create } from 'zustand'
import { api, triggerUnauthorized } from '../lib/apiClient'
import { useSettings } from './settingsStore'
import { useThreads } from './threadStore'
import { useToasts } from './toastStore'

export type Message = {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at?: string
  model?: string | null
  token_in?: number | null
  token_out?: number | null
  cost_usd?: string | number | null
  api_calls?: number | null
  agents?: { activated?: string[]; count?: number } | null
  tools?: { used?: string[]; count?: number } | null
  metadata?: Record<string, any> | null
  parent_id?: number | null
  thinking?: string | null
}

type MessagesState = {
  messages: Message[]
  refresh: (threadId: number | string) => Promise<void>
  send: (
    threadId: number | string,
    content: string,
    user_name: string,
    stream: boolean
  ) => Promise<void>
  edit: (id: number, content: string) => Promise<void>
  del: (id: number) => Promise<void>
  branch: (
    threadId: number | string,
    parentId: number,
    content: string,
    user_name: string
  ) => Promise<void>
  fork: (threadId: number | string, atMessage: Message, title: string) => Promise<number | null>
  streamingActive: boolean
  stop: () => void
  controller: AbortController | null
  liveActiveAgent: string | null
  liveAgents: string[]
  liveTool: { name: string; status: 'running' | 'done' } | null
  turnStats: {
    token_in?: number | null
    token_out?: number | null
    cost_usd?: string | number | null
    api_calls?: number | null
    model?: string | null
    provider?: string | null
    agents?: string[]
    tools?: string[]
  } | null
}

export const useMessages = create<MessagesState>((set, get) => ({
  messages: [],
  streamingActive: false,
  controller: null,
  liveActiveAgent: null,
  liveAgents: [],
  liveTool: null,
  turnStats: null,
  stop: () => {
    const c = get().controller
    if (c) {
      try {
        c.abort()
      } catch {
        /* ignore */
      }
      set({ controller: null, streamingActive: false, liveActiveAgent: null, liveTool: null })
    }
  },
  refresh: async (threadId) => {
    const { ok, data } = await api(`/api/threads/${threadId}/messages`)
    if (ok && Array.isArray(data)) set({ messages: data })
  },
  send: async (threadId, content, user_name, stream) => {
    const threadsState = useThreads.getState()
    const isDraft = String(threadId).startsWith('draft_')

    let actualThreadId: number = threadId as number

    if (isDraft) {
      const newThreadId = await threadsState.createThread('New Thread')
      if (!newThreadId) {
        useToasts.getState().push({ type: 'error', text: 'Failed to create thread' })
        return
      }
      actualThreadId = newThreadId
      threadsState.setCurrent(newThreadId)
    } else {
      actualThreadId = threadId as number
    }

    if (!stream) {
      await api(`/api/threads/${actualThreadId}/messages`, {
        method: 'POST',
        json: { content, user_name },
      })
      await get().refresh(actualThreadId)
      return
    }
    await get().refresh(actualThreadId)
    const live: Message = { id: -1, role: 'assistant', content: '' }
    set((s) => ({
      messages: [...s.messages, live],
      streamingActive: true,
      liveActiveAgent: null,
      liveAgents: [],
      liveTool: null,
      turnStats: null,
    }))
    const token = localStorage.getItem('token') || ''
    const url = new URL(`/api/threads/${actualThreadId}/messages/stream`, window.location.origin)
    if (token) url.searchParams.set('token', token)
    const ctrl = new AbortController()
    set({ controller: ctrl })
    const decoder = new TextDecoder()
    let buf = ''
    let thinkingShown = false
    let finished = false
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ content, user_name }),
        signal: ctrl.signal,
      })
      if (resp.status === 401) {
        try {
          triggerUnauthorized()
        } catch {
          /* ignore */
        }
        finished = true
      } else if (!resp.ok) {
        useToasts.getState().push({ type: 'error', text: `Stream failed (${resp.status})` })
        finished = true
      } else {
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
                set((st) => ({
                  messages: [...st.messages, { id: -2, role: 'assistant', content: 'Thinking…' }],
                }))
              }
              continue
            }
            if (ev === 'agent' && data) {
              try {
                const obj = JSON.parse(data)
                const name = obj.name || obj.agent || ''
                if (name)
                  set((st) => ({
                    liveActiveAgent: name,
                    liveAgents: Array.from(new Set([...st.liveAgents, name])),
                  }))
              } catch {
                /* ignore invalid JSON */
              }
              continue
            }
            if (ev === 'tool_call' && data) {
              try {
                const obj = JSON.parse(data)
                const tool = obj.name || obj.tool || ''
                const status = obj.status || ''
                if (tool) {
                  if (status === 'start') set({ liveTool: { name: tool, status: 'running' } })
                  else if (status === 'end') set({ liveTool: { name: tool, status: 'done' } })
                  else set({ liveTool: { name: tool, status: 'running' } })
                }
              } catch {
                /* ignore invalid JSON */
              }
              continue
            }
            if (ev === 'done') {
              finished = true
              try {
                setTimeout(() => {
                  useMessages.setState({ liveTool: null, liveActiveAgent: null })
                }, 1000)
              } catch {
                /* ignore */
              }
              break
            }
            if (ev === 'error') {
              try {
                if (data) {
                  const obj = JSON.parse(data)
                  const msg = obj.detail || obj.error || (typeof obj === 'string' ? obj : '')
                  if (msg) useToasts.getState().push({ type: 'error', text: String(msg) })
                }
              } catch {
                /* ignore invalid JSON */
              }
              finished = true
              break
            }
            if (ev === 'message' && data) {
              try {
                const obj = JSON.parse(data)
                if (obj.delta) {
                  set((s) => {
                    const arr = s.messages.slice()
                    if (thinkingShown) {
                      const last = arr[arr.length - 1]
                      if (last && last.id === -2) {
                        arr.pop()
                        thinkingShown = false
                      }
                    }
                    const last = arr[arr.length - 1]
                    if (last && last.id === -1) last.content += obj.delta
                    return { messages: arr }
                  })
                } else if (obj.id) {
                  const provider = obj?.metadata?.provider || null
                  const agents = (obj?.agents?.activated || []) as string[]
                  const tools = (obj?.tools?.used || []) as string[]
                  set({
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
                  await get().refresh(actualThreadId)
                }
              } catch {
                /* ignore invalid JSON */
              }
            }
          }
          if (finished) break
        }
      }
    } catch {
      // AbortError or network error - ignore
    } finally {
      set({ controller: null, streamingActive: false, liveActiveAgent: null, liveTool: null })
      await get().refresh(actualThreadId)
    }
  },
  edit: async (id, content) => {
    set((s) => ({ messages: s.messages.map((x) => (x.id === id ? { ...x, content } : x)) }))
    const res = await api(`/api/messages/${id}`, {
      method: 'PATCH',
      json: { content, branch: true },
    })
    if (!res.ok) {
      try {
        useToasts.getState().push({ type: 'error', text: 'Edit failed' })
      } catch {
        /* ignore */
      }
    }
    const tid = useThreads.getState().currentId
    if (tid && typeof tid === 'number') await get().refresh(tid)
  },
  del: async (id) => {
    set((s) => ({ messages: s.messages.filter((x) => x.id !== id) }))
    await api(`/api/messages/${id}`, { method: 'DELETE' })
    const tid = useThreads.getState().currentId
    if (tid && typeof tid === 'number') await get().refresh(tid)
  },
  branch: async (threadId, parentId, content, user_name) => {
    if (typeof threadId !== 'number') return
    await api(`/api/threads/${threadId}/messages`, {
      method: 'POST',
      json: { content, user_name, parent_id: parentId },
    })
  },
  fork: async (threadId, atMessage, title) => {
    if (typeof threadId !== 'number') return null
    const { ok, data } = await api(`/api/threads/${threadId}/messages`)
    if (!ok || !Array.isArray(data)) return null
    const subset = data.filter((x: Message) => x.id <= atMessage.id)
    const payload = {
      title: title || `Fork of #${threadId}`,
      messages: subset.map((x: Message) => ({
        id: x.id,
        role: x.role,
        content: x.content,
        model: x.model || null,
        token_in: x.token_in ?? null,
        token_out: x.token_out ?? null,
        cost_usd: x.cost_usd ?? null,
        agents: x.agents ?? null,
        tools: x.tools ?? null,
        api_calls: x.api_calls ?? null,
        parent_id: x.parent_id ?? null,
        metadata: x.metadata ?? null,
      })),
    }
    const res = await api('/api/threads/import', { method: 'POST', json: payload })
    if (res.ok && res.data?.id) return res.data.id
    return null
  },
}))

export const useMessagesSelector = <T>(selector: (state: MessagesState) => T): T =>
  useMessages(selector)

export const useMessagesActions = () =>
  useMessages((state) => ({
    refresh: state.refresh,
    send: state.send,
    edit: state.edit,
    del: state.del,
    branch: state.branch,
    fork: state.fork,
    stop: state.stop,
  }))

export const useStreamingState = () =>
  useMessages((state) => ({
    streamingActive: state.streamingActive,
    liveActiveAgent: state.liveActiveAgent,
    liveAgents: state.liveAgents,
    liveTool: state.liveTool,
    turnStats: state.turnStats,
  }))
