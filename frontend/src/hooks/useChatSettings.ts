import { useEffect } from 'react'
import { api } from '../lib/apiClient'
import { useSettings } from '../stores/settingsStore'

export function useChatSettings(token: string | null) {
  useEffect(() => {
    ;(async () => {
      const t = token || localStorage.getItem('token') || ''
      const url = t ? `/api/settings?token=${encodeURIComponent(t)}` : '/api/settings'
      const { ok, data } = await api(url)
      if (ok && (data as any)?.settings) {
        const s = (data as any).settings
        useSettings.setState((st) => ({
          ...st,
          showThinking: !!s.show_thinking,
          showTimestamps: !!s.show_timestamps,
          showModel: !!s.show_model_tag,
          showMeta: !!s.show_metadata_panel,
          theme: s.theme || st.theme,
          streaming: s.streaming || st.streaming,
          mode: s.mode || st.mode,
        }))
      }
    })()
  }, [token])
}
