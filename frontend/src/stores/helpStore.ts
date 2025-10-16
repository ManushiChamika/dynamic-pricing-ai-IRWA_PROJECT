import { create } from 'zustand'

export const useHelp = create<{ open: boolean; openHelp: () => void; close: () => void }>((set) => ({
  open: false,
  openHelp: () => set({ open: true }),
  close: () => set({ open: false })
}))
