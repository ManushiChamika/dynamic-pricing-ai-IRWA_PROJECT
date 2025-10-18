import { create } from 'zustand'

export const useCatalogStore = create<{
  catalogOpen: boolean
  setCatalogOpen: (open: boolean) => void
}>((set) => ({
  catalogOpen: false,
  setCatalogOpen: (open) => set({ catalogOpen: open }),
}))
