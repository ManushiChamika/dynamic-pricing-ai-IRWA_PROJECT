import { create } from 'zustand'

export type Toast = { id: number; type: 'info' | 'success' | 'error'; text: string }

export const useToasts = create<{
  toasts: Toast[]
  push: (t: { text: string; type?: 'info' | 'success' | 'error' }) => void
  remove: (id: number) => void
}>((set) => ({
  toasts: [],
  push: ({ text, type = 'info' }) =>
    set((s) => ({
      toasts: [...s.toasts, { id: Date.now() + Math.random(), text, type }],
    })),
  remove: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))
