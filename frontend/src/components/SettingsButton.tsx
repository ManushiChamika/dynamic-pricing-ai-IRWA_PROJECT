import React, { useState, lazy, Suspense } from 'react'
import { Button } from './ui/button'
import { useSettings, type Settings } from '../stores/settingsStore'
import { api } from '../lib/apiClient'

const SettingsModal = lazy(() => import('./SettingsModal').then(m => ({ default: m.SettingsModal })))

export function SettingsButton() {
  const [open, setOpen] = useState(false)
  const s = useSettings()
  const update = async (partial: Partial<Settings>) => {
    useSettings.setState(partial as any)
    const token = localStorage.getItem('token') || ''
    if (token) {
      const map: Record<string, string> = {
        showModel: 'show_model_tag',
        showTimestamps: 'show_timestamps',
        showMeta: 'show_metadata_panel',
        showThinking: 'show_thinking',
        theme: 'theme',
        streaming: 'streaming',
        mode: 'mode',
      }
      const serverSettings: Record<string, any> = {}
      Object.entries(partial).forEach(([k, v]) => {
        const key = (map as any)[k]
        if (key) serverSettings[key] = v
      })
      if (Object.keys(serverSettings).length) {
        await api('/api/settings', { method: 'PUT', json: { token, settings: serverSettings } })
      }
    }
  }
  return (
      <>
        <Button variant="ghost" size="sm" onClick={() => setOpen(true)} aria-label="Open settings">Settings</Button>
        <Suspense fallback={null}>
          <SettingsModal 
            open={open} 
            onOpenChange={setOpen}
            settings={s as any}
            onSettingsChange={(newSettings) => update(newSettings)}
          />
        </Suspense>
      </>
  )
}
