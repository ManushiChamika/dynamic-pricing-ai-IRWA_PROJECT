import React, { useEffect, lazy, Suspense } from 'react'
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

const SettingsModal = lazy(() =>
  import('./components/SettingsModal').then((m) => ({ default: m.SettingsModal }))
)


export default function App() {
  const { theme, settingsOpen, setSettingsOpen, ...settings } = useSettings()
  const { catalogOpen, setCatalogOpen } = useCatalogStore()
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
        <CatalogModal
          open={catalogOpen}
          onOpenChange={setCatalogOpen}
        />
        <Toasts />
      </div>
    </ErrorBoundary>
  )
}
