import { create } from 'zustand'
import { useThreads } from './threadStore'
import { useToasts } from './toastStore'
import { streamMessage } from '../lib/sseClient'
import {
  fetchMessages,
  sendMessage,
  editMessage,
  deleteMessage,
  branchMessage,
} from '../lib/messageApi'

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
    const data = await fetchMessages(threadId)
    set({ messages: data })
  },
  send: async (threadId, content, user_name, stream) => {
    const threadsState = useThreads.getState()
    const isDraft = String(threadId).startsWith('draft_')

    const userMsg: Message = { id: -1, role: 'user', content }
    const live: Message = { id: -2, role: 'assistant', content: '' }
    let thinkingShown = false

    set((s) => ({
      messages: [...s.messages, userMsg, live],
      streamingActive: true,
      liveActiveAgent: null,
      liveAgents: [],
      liveTool: null,
      turnStats: null,
    }))

    let actualThreadId: number = threadId as number

    if (isDraft) {
      const newThreadId = await threadsState.createThread('New Thread')
      if (!newThreadId) {
        useToasts.getState().push({
          type: 'error',
          text: 'Failed to create thread. Check console and ensure backend is running.',
        })
        set((s) => ({
          messages: s.messages.filter((m) => m.id !== -1 && m.id !== -2),
          streamingActive: false,
        }))
        return
      }
      actualThreadId = newThreadId
      threadsState.setCurrent(newThreadId)
    } else {
      actualThreadId = threadId as number
    }

    if (!stream) {
      await sendMessage(actualThreadId, content, user_name)
      await get().refresh(actualThreadId)
      return
    }

    const ctrl = new AbortController()
    set({ controller: ctrl })

    try {
      await streamMessage(
        actualThreadId,
        content,
        user_name,
        (update) => {
          set((s) => {
            if (update.thinking) {
              if (!thinkingShown) {
                thinkingShown = true
                return {
                  messages: [...s.messages, { id: -3, role: 'assistant', content: 'Thinking…' }],
                }
              }
            }

            if (update.delta) {
              const arr = s.messages.slice()
              if (thinkingShown) {
                const lastThinking = arr[arr.length - 1]
                if (lastThinking && lastThinking.id === -3) {
                  arr.pop()
                  thinkingShown = false
                }
              }
              const last = arr[arr.length - 1]
              if (last && last.id === -2) last.content += update.delta
              return { messages: arr }
            }

            if (update.agent) {
              return {
                liveActiveAgent: update.agent,
                liveAgents: Array.from(new Set([...s.liveAgents, update.agent])),
              }
            }

            if (update.tool) {
              return { liveTool: update.tool }
            }

            if (update.turnStats) {
              return { turnStats: update.turnStats }
            }

            if (update.threadRenamed) {
              useThreads
                .getState()
                .updateThreadTitleLocal(update.threadRenamed.thread_id, update.threadRenamed.title)
              return s
            }

            if (update.done) {
              return {
                controller: null,
                streamingActive: false,
                liveActiveAgent: null,
                liveTool: null,
              }
            }

            return s
          })
        },
        ctrl
      )
    } catch {
      // AbortError or network error - ignore
    } finally {
      set({ controller: null, streamingActive: false, liveActiveAgent: null, liveTool: null })
      await get().refresh(actualThreadId)
    }
  },
  edit: async (id, content) => {
    set((s) => ({ messages: s.messages.map((x) => (x.id === id ? { ...x, content } : x)) }))
    const ok = await editMessage(id, content)
    if (!ok) {
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
    await deleteMessage(id)
    const tid = useThreads.getState().currentId
    if (tid && typeof tid === 'number') await get().refresh(tid)
  },
  branch: async (threadId, parentId, content, user_name) => {
    if (typeof threadId !== 'number') return
    await branchMessage(threadId, parentId, content, user_name)
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
