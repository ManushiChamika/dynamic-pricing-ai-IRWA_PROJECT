import { useGlobalShortcuts, isInInput } from '@/lib/hooks'
import { useMessagesActions, useStreamingState, useMessages } from '../stores/messageStore'
import { useThreads } from '../stores/threadStore'
import { useSettings } from '../stores/settingsStore'
import { useHelp } from '../stores/helpStore'
import { usePrompt } from '../stores/promptStore'

export function useChatKeyboardShortcuts(
  currentId: number | string | null,
  streamingActive: boolean,
  streaming: string | undefined,
  setInput: (value: string) => void
) {
  const { send, stop, refresh } = useMessagesActions()
  const messages = useMessages((state) => state.messages)

  useGlobalShortcuts([
    {
      handler: (e) => {
        if (e.key === 'Escape' && streamingActive) {
          stop()
        }
      },
    },
    {
      handler: (e) => {
        if (e.ctrlKey && e.key === '/') {
          e.preventDefault()
          useHelp.getState().openHelp()
        }
      },
    },
    {
      handler: (e) => {
        if (e.ctrlKey && e.key.toLowerCase() === 'b') {
          e.preventDefault()
          document
            .querySelector<HTMLButtonElement>('.sidebar button[aria-label*="sidebar"]')
            ?.click()
        }
      },
    },
    {
      handler: (e) => {
        if (e.ctrlKey && e.key.toLowerCase() === 'n') {
          e.preventDefault()
          useThreads.getState().createDraftThread()
        }
      },
    },
    {
      handler: (e) => {
        if (isInInput(document.activeElement)) {
          const composer = document.querySelector<HTMLTextAreaElement>('.composer textarea')
          if (composer && document.activeElement === composer) {
            if (e.ctrlKey && e.key === 'Enter') {
              e.preventDefault()
              if (!streaming || streamingActive) return
              const value = composer.value.trim()
              if (currentId && value) {
                send(currentId, value, 'user', streaming === 'sse')
                composer.value = ''
                ;(composer as any).dispatchEvent(new Event('input', { bubbles: true }))
                setInput('')
              }
            }
            if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'k') {
              e.preventDefault()
              composer.value = ''
              ;(composer as any).dispatchEvent(new Event('input', { bubbles: true }))
              setInput('')
            }
          }
        }
      },
    },
    {
      handler: (e) => {
        if (
          !isInInput(document.activeElement) &&
          e.ctrlKey &&
          e.key.toLowerCase() === 'k' &&
          !e.shiftKey
        ) {
          e.preventDefault()
          document.querySelector<HTMLTextAreaElement>('.composer textarea')?.focus()
        }
      },
    },
    {
      handler: (e) => {
        if (!isInInput(document.activeElement) && e.ctrlKey && e.key.toLowerCase() === 'l') {
          e.preventDefault()
          useSettings.setState((s) => ({ theme: s.theme === 'dark' ? 'light' : 'dark' }))
        }
      },
    },
    {
      handler: (e) => {
        if (
          !isInInput(document.activeElement) &&
          e.ctrlKey &&
          e.shiftKey &&
          e.key.toLowerCase() === 'e'
        ) {
          e.preventDefault()
          const btn = document.querySelector<HTMLButtonElement>(
            'button[aria-label="Export thread"]'
          )
          if (btn && !btn.disabled) btn.click()
        }
      },
    },
    {
      handler: (e) => {
        if (
          !isInInput(document.activeElement) &&
          e.ctrlKey &&
          e.shiftKey &&
          e.key.toLowerCase() === 'i'
        ) {
          e.preventDefault()
          const input = document.querySelector<HTMLInputElement>(
            'input[aria-label="Import thread file"]'
          )
          if (input && !input.disabled) input.click()
        }
      },
    },
    {
      handler: (e) => {
        if (!isInInput(document.activeElement) && e.ctrlKey && e.key === ',') {
          e.preventDefault()
          useSettings.getState().setSettingsOpen(true)
        }
      },
    },
  ])
}
