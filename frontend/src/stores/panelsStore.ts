import { create } from 'zustand'

interface PanelsState {
  pricesCollapsed: boolean
  togglePricesCollapsed: () => void
  setPricesCollapsed: (collapsed: boolean) => void
}

export const usePanels = create<PanelsState>((set) => ({
  pricesCollapsed: localStorage.getItem('pricesCollapsed') === '1',
  togglePricesCollapsed: () =>
    set((state) => {
      const next = !state.pricesCollapsed
      localStorage.setItem('pricesCollapsed', next ? '1' : '0')
      return { pricesCollapsed: next }
    }),
  setPricesCollapsed: (collapsed: boolean) => {
    localStorage.setItem('pricesCollapsed', collapsed ? '1' : '0')
    set({ pricesCollapsed: collapsed })
  },
}))
