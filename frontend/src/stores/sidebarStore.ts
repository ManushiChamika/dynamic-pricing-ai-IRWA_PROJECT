import { create } from 'zustand'

interface SidebarState {
  collapsed: boolean
  toggleCollapsed: () => void
  setCollapsed: (collapsed: boolean) => void
}

export const useSidebar = create<SidebarState>((set) => ({
  collapsed: localStorage.getItem('sidebarCollapsed') === '1',
  toggleCollapsed: () =>
    set((state) => {
      const newCollapsed = !state.collapsed
      localStorage.setItem('sidebarCollapsed', newCollapsed ? '1' : '0')
      return { collapsed: newCollapsed }
    }),
  setCollapsed: (collapsed: boolean) => {
    localStorage.setItem('sidebarCollapsed', collapsed ? '1' : '0')
    set({ collapsed })
  },
}))
