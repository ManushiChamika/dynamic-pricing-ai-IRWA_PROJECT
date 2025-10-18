import React, { useEffect, lazy, Suspense } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { PricesPanel } from './components/PricesPanel'
import { ChatPane } from './components/ChatPane'
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

const SettingsModal = lazy(() =>
  import('./components/SettingsModal').then((m) => ({ default: m.SettingsModal }))
)

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
    document.documentElement.classList.toggle('light', theme === 'light')
    localStorage.setItem('theme', theme)
  }, [theme])
  return (
    <ErrorBoundary>
      <div className="flex h-full">
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
      </div>
    </ErrorBoundary>
  )
}
