import { create } from 'zustand'

export type Settings = {
  theme: 'dark' | 'light'
  showModel: boolean
  showTimestamps: boolean
  showMeta: boolean
  showThinking: boolean
  mode: 'user' | 'developer'
  streaming: 'sse' | 'none'
}

export const useSettings = create<Settings & { set: (p: Partial<Settings>) => void; settingsOpen: boolean; setSettingsOpen: (open: boolean) => void }>((set) => ({
  theme: (localStorage.getItem('theme') as any) || 'dark',
  showModel: true,
  showTimestamps: false,
  showMeta: false,
  showThinking: false,
  mode: 'user',
  streaming: 'sse',
  settingsOpen: false,
  set: (p) => set(s => ({ ...s, ...p })),
  setSettingsOpen: (open) => set({ settingsOpen: open })
}))
