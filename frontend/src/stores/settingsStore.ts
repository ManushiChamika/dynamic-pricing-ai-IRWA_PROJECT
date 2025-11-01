import { create } from 'zustand'

export type Theme = 'dark' | 'light' | 'ocean' | 'forest' | 'sunset' | 'midnight' | 'rose'

export type Settings = {
  theme: Theme
  showModel: boolean
  showTimestamps: boolean
  showMeta: boolean
  showThinking: boolean
  mode: 'user' | 'developer'
  streaming: 'sse' | 'none'
}

export const useSettings = create<
  Settings & {
    set: (p: Partial<Settings>) => void
    settingsOpen: boolean
    setSettingsOpen: (open: boolean) => void
  }
>((set) => ({
  theme: (localStorage.getItem('theme') as Theme) || 'dark',
  showModel: true,
  showTimestamps: false,
  showMeta: false,
  showThinking: false,
  mode: 'user',
  streaming: 'sse',
  settingsOpen: false,
  set: (p) => set((s) => ({ ...s, ...p })),
  setSettingsOpen: (open) => set({ settingsOpen: open }),
}))

export const useTheme = () => useSettings((state) => state.theme)

export const useDisplaySettings = () =>
  useSettings((state) => ({
    showModel: state.showModel,
    showTimestamps: state.showTimestamps,
    showMeta: state.showMeta,
    showThinking: state.showThinking,
  }))

export const useAppMode = () =>
  useSettings((state) => ({ mode: state.mode, streaming: state.streaming }))

export const useSettingsActions = () =>
  useSettings((state) => ({
    set: state.set,
    setSettingsOpen: state.setSettingsOpen,
  }))
