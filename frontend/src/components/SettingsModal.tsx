import React from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog'
import { Settings } from '../lib/types'
import { SettingToggle } from './settings/SettingToggle'

interface SettingsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  settings: Settings
  onSettingsChange: (settings: Settings) => void
}

function SettingsModalComponent({
  open,
  onOpenChange,
  settings,
  onSettingsChange,
}: SettingsModalProps) {
  const updateSetting = <K extends keyof Settings>(key: K, value: Settings[K]) => {
    const newSettings = { ...settings, [key]: value }
    onSettingsChange(newSettings)
    localStorage.setItem('chat-settings', JSON.stringify(newSettings))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>Configure your chat experience</DialogDescription>
        </DialogHeader>
        <div className="space-y-6 py-4">
          <SettingToggle
            label="Theme"
            description={settings.theme === 'dark' ? 'Dark mode' : 'Light mode'}
            checked={settings.theme === 'dark'}
            onCheckedChange={(checked) => updateSetting('theme', checked ? 'dark' : 'light')}
          />
          <SettingToggle
            label="Show Model Name"
            description="Display model name in messages"
            checked={settings.showModel}
            onCheckedChange={(checked) => updateSetting('showModel', checked)}
          />
          <SettingToggle
            label="Show Timestamps"
            description="Display message timestamps"
            checked={settings.showTimestamps}
            onCheckedChange={(checked) => updateSetting('showTimestamps', checked)}
          />
          <SettingToggle
            label="Show Info Icon"
            description="Display metadata info icon on messages"
            checked={settings.showMeta}
            onCheckedChange={(checked) => updateSetting('showMeta', checked)}
          />
          <SettingToggle
            label="Show Thinking"
            description="Display extended thinking process"
            checked={settings.showThinking}
            onCheckedChange={(checked) => updateSetting('showThinking', checked)}
          />
          <SettingToggle
            label="Streaming Mode"
            description={settings.streaming === 'sse' ? 'Server-Sent Events' : 'No streaming'}
            checked={settings.streaming === 'sse'}
            onCheckedChange={(checked) => updateSetting('streaming', checked ? 'sse' : 'none')}
          />
          {settings.mode === 'developer' && (
            <div className="rounded-lg border border-border bg-muted/50 p-3">
              <div className="text-sm font-medium">Developer Mode</div>
              <p className="text-xs text-muted-foreground mt-1">Advanced settings enabled</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export const SettingsModal = React.memo(SettingsModalComponent)
