import { create } from 'zustand'
import * as threadApi from '../lib/threadApi'

export type Thread = { id: number; title: string }

export type ThreadsState = {
  threads: Thread[]
  currentId: number | string | null
  draftId: string | null
  setCurrent: (id: number | string | null) => void
  createDraftThread: () => void
  refresh: () => Promise<void>
  createThread: (title?: string) => Promise<number | null>
  deleteThread: (id: number) => Promise<void>
  renameThread: (id: number, title: string) => Promise<void>
}

const DRAFT_ID_PREFIX = 'draft_'
let draftCounter = 0

const isDraftThread = (id: number | string | null): id is string => {
  return typeof id === 'string' && id.startsWith(DRAFT_ID_PREFIX)
}

export const useThreads = create<ThreadsState>((set, get) => ({
  threads: [],
  currentId: null,
  draftId: null,
  setCurrent: (id) => {
    set({ currentId: id })
    if (id && !String(id).startsWith(DRAFT_ID_PREFIX)) {
      localStorage.setItem('lastThreadId', String(id))
    }
  },
  createDraftThread: () => {
    const newDraftId = `${DRAFT_ID_PREFIX}${++draftCounter}`
    set({ currentId: newDraftId, draftId: newDraftId })
  },
  refresh: async () => {
    const threads = await threadApi.loadThreads()
    set({ threads })
  },
  createThread: async (title?: string) => {
    const id = await threadApi.createThread(title)
    if (id) {
      await get().refresh()
      set({ draftId: null })
      return id
    }
    return null
  },
  deleteThread: async (id: number) => {
    await threadApi.deleteThread(id)
    await get().refresh()
    const cur = get().currentId
    if (cur === id) set({ currentId: null })
  },
  renameThread: async (id: number, title: string) => {
    await threadApi.renameThread(id, title)
    await get().refresh()
  },
}))

export const useCurrentThread = () => useThreads((state) => state.currentId)

export const useThreadList = () => useThreads((state) => state.threads)

export const useDraftId = () => useThreads((state) => state.draftId)

export const useThreadActions = () =>
  useThreads((state) => ({
    setCurrent: state.setCurrent,
    refresh: state.refresh,
    createThread: state.createThread,
    createDraftThread: state.createDraftThread,
    deleteThread: state.deleteThread,
    renameThread: state.renameThread,
  }))

export { isDraftThread }
