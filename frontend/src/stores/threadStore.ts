import { create } from 'zustand'
import { api } from '../lib/apiClient'

export type Thread = { id: number; title: string }

export type ThreadsState = {
  threads: Thread[]
  currentId: number | null
  setCurrent: (id: number | null) => void
  refresh: () => Promise<void>
  createThread: (title?: string) => Promise<void>
  deleteThread: (id: number) => Promise<void>
  renameThread: (id: number, title: string) => Promise<void>
}

export const useThreads = create<ThreadsState>((set, get) => ({
  threads: [],
  currentId: null,
  setCurrent: (id) => { set({ currentId: id }); if (id) localStorage.setItem('lastThreadId', String(id)) },
  refresh: async () => {
    const { ok, data } = await api('/api/threads')
    if (ok && Array.isArray(data)) set({ threads: data })
  },
  createThread: async (title?: string) => {
    const { ok, data } = await api('/api/threads', { method: 'POST', json: { title: title || 'New Thread' } })
    if (ok && data) {
      await get().refresh()
      set({ currentId: data.id })
    }
  },
  deleteThread: async (id: number) => {
    await api(`/api/threads/${id}`, { method: 'DELETE' })
    await get().refresh()
    const cur = get().currentId
    if (cur === id) set({ currentId: null })
  },
  renameThread: async (id: number, title: string) => {
    await api(`/api/threads/${id}`, { method: 'PATCH', json: { title } })
    await get().refresh()
  }
}))
