import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog'
import { Switch } from './ui/switch'
import { Settings } from '../lib/types'

interface SettingsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  settings: Settings
  onSettingsChange: (settings: Settings) => void
}

export function SettingsModal({
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
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <label className="text-sm font-medium">Theme</label>
              <p className="text-sm text-muted-foreground">
                {settings.theme === 'dark' ? 'Dark mode' : 'Light mode'}
              </p>
            </div>
            <Switch
              checked={settings.theme === 'dark'}
              onCheckedChange={(checked) => updateSetting('theme', checked ? 'dark' : 'light')}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <label className="text-sm font-medium">Show Model Name</label>
              <p className="text-sm text-muted-foreground">Display model name in messages</p>
            </div>
            <Switch
              checked={settings.showModel}
              onCheckedChange={(checked) => updateSetting('showModel', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <label className="text-sm font-medium">Show Timestamps</label>
              <p className="text-sm text-muted-foreground">Display message timestamps</p>
            </div>
            <Switch
              checked={settings.showTimestamps}
              onCheckedChange={(checked) => updateSetting('showTimestamps', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <label className="text-sm font-medium">Show Info Icon</label>
              <p className="text-sm text-muted-foreground">
                Display metadata info icon on messages
              </p>
            </div>
            <Switch
              checked={settings.showMeta}
              onCheckedChange={(checked) => updateSetting('showMeta', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <label className="text-sm font-medium">Show Thinking</label>
              <p className="text-sm text-muted-foreground">Display extended thinking process</p>
            </div>
            <Switch
              checked={settings.showThinking}
              onCheckedChange={(checked) => updateSetting('showThinking', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <label className="text-sm font-medium">Streaming Mode</label>
              <p className="text-sm text-muted-foreground">
                {settings.streaming === 'sse' ? 'Server-Sent Events' : 'No streaming'}
              </p>
            </div>
            <Switch
              checked={settings.streaming === 'sse'}
              onCheckedChange={(checked) => updateSetting('streaming', checked ? 'sse' : 'none')}
            />
          </div>
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
