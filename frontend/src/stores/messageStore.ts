// Message store for chat functionality
import { create } from 'zustand'

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
  refresh: (threadId: number) => Promise<void>
  send: (threadId: number, content: string, user_name: string, stream: boolean) => Promise<void>
  edit: (id: number, content: string) => Promise<void>
  del: (id: number) => Promise<void>
  branch: (threadId: number, parentId: number, content: string, user_name: string) => Promise<void>
  fork: (threadId: number, atMessage: Message, title: string) => Promise<number | null>
  streamingActive: boolean
  stop: () => void
  controller: AbortController | null
  liveActiveAgent: string | null
  liveAgents: string[]
  liveTool: { name: string; status: 'running' | 'done' } | null
  turnStats: { token_in?: number | null; token_out?: number | null; cost_usd?: string | number | null; api_calls?: number | null; model?: string | null; provider?: string | null; agents?: string[]; tools?: string[] } | null
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
      try { c.abort() } catch { /* ignore */ }
      set({ controller: null, streamingActive: false, liveActiveAgent: null, liveTool: null })
    }
  },
  refresh: async (threadId) => {
    // Implement API call here
    // For now, placeholder
    set({ messages: [] })
  },
  send: async (threadId, content, user_name, stream) => {
    // Implement send logic
  },
  edit: async (id, content) => {
    // Implement edit logic
  },
  del: async (id) => {
    // Implement delete logic
  },
  branch: async (threadId, parentId, content, user_name) => {
    // Implement branch logic
  },
  fork: async (threadId, atMessage, title) => {
    // Implement fork logic
    return null
  }
}))