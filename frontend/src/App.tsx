import React, { useEffect, lazy, Suspense } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { PricesPanel } from './components/PricesPanel'
import { LayoutProvider } from './contexts/LayoutContext'
import { ChatPane } from './components/chat/ChatPane'
import { Sidebar } from './components/Sidebar'
import { PromptModal } from './components/PromptModal'
import { ConfirmModal } from './components/ConfirmModal'
import { HelpModal } from './components/HelpModal'
import { Toasts } from './components/Toasts'
import { ErrorBoundary } from './components/ErrorBoundary'
import { useSettings } from './stores/settingsStore'
import { CatalogModal } from './components/CatalogModal'
import { useCatalogStore } from './stores/catalogStore'
import { useThreadActions, useCurrentThread } from './stores/threadStore'
import { useSidebar } from './stores/sidebarStore'
import { usePanels } from './stores/panelsStore'

const SettingsModal = lazy(() =>
  import('./components/SettingsModal').then((m) => ({ default: m.SettingsModal }))
)

function MobileBackdrop() {
  const { collapsed, setCollapsed } = useSidebar()
  const { pricesCollapsed, setPricesCollapsed } = usePanels()
  const anyOpen = (!collapsed || !pricesCollapsed)
  if (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(min-width: 768px)').matches) {
    return null
  }
  if (!anyOpen) return null
  return (
    <div
      onClick={() => {
        setCollapsed(true)
        setPricesCollapsed(true)
      }}
      className="fixed inset-0 z-30 bg-black/40 backdrop-blur-[1px] md:hidden"
      aria-hidden="true"
    />
  )
}

export default function App() {
  const { threadId } = useParams<{ threadId?: string }>()
  const navigate = useNavigate()
  const { theme, settingsOpen, setSettingsOpen, ...settings } = useSettings()
  const { catalogOpen, setCatalogOpen } = useCatalogStore()
  const { setCurrent } = useThreadActions()
  const currentId = useCurrentThread()

  useEffect(() => {
    if (threadId) {
      const numericId = parseInt(threadId, 10)
      if (!isNaN(numericId) && numericId !== currentId) {
        setCurrent(numericId)
      } else if (isNaN(numericId)) {
        navigate('/chat', { replace: true })
      }
    }
  }, [threadId, setCurrent, navigate, currentId])

   useEffect(() => {
     document.documentElement.classList.remove('light', 'dark', 'ocean', 'forest', 'sunset', 'midnight', 'rose')
     document.documentElement.classList.add(theme)
     localStorage.setItem('theme', theme)
   }, [theme])

   useEffect(() => {
     if (typeof window === 'undefined' || !window.matchMedia) return
     const isMobile = window.matchMedia('(max-width: 767px)').matches
     if (isMobile) {
       if (localStorage.getItem('sidebarCollapsed') === null) useSidebar.getState().setCollapsed(true)
       if (localStorage.getItem('pricesCollapsed') === null) usePanels.getState().setPricesCollapsed(true)
     }
     const onKey = (e: KeyboardEvent) => {
       if (e.key === 'Escape') {
         useSidebar.getState().setCollapsed(true)
         usePanels.getState().setPricesCollapsed(true)
       }
     }
     window.addEventListener('keydown', onKey)
     return () => window.removeEventListener('keydown', onKey)
   }, [])
  return (
    <ErrorBoundary>
       <LayoutProvider>
         <div className="relative flex h-full overflow-hidden">
        <Sidebar />
        <ChatPane />
        <PricesPanel />
        <PromptModal />
        <ConfirmModal />
        <HelpModal />
        <Suspense fallback={null}>
          <SettingsModal
            open={settingsOpen}
            onOpenChange={setSettingsOpen}
            settings={{ theme, ...settings }}
            onSettingsChange={(newSettings) => useSettings.getState().set(newSettings)}
          />
        </Suspense>
        <CatalogModal open={catalogOpen} onOpenChange={setCatalogOpen} />
        <Toasts />
        <MobileBackdrop />
        </div>
       </LayoutProvider>
    </ErrorBoundary>
  )
}
