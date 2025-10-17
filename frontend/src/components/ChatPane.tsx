import React, { useEffect, useRef, useState, useMemo } from 'react'
import { useGlobalShortcuts, isInInput } from '@/lib/hooks'
import { SCROLL_STICKY_THRESHOLD_PX } from '@/lib/constants'
import { Button } from './ui/button'
import { useMessages, useMessagesActions, useStreamingState } from '../stores/messageStore'
import { useThreads, useCurrentThread } from '../stores/threadStore'
import { useSettings, useDisplaySettings, useAppMode } from '../stores/settingsStore'
import { useAuthToken } from '../stores/authStore'
import { useHelp } from '../stores/helpStore'
import { usePrompt } from '../stores/promptStore'
import { useConfirm } from '../stores/confirmStore'
import { useToasts } from '../stores/toastStore'
import { SummaryIndicator } from './SummaryIndicator'
import { AuthControls } from './AuthControls'
import { SettingsButton } from './SettingsButton'
import { MessageView } from './MessageView'
import { HeaderOverflowMenu, type HeaderMenuAction } from './HeaderOverflowMenu'
import { api } from '../lib/apiClient'

export function ChatPane() {
  const messages = useMessages((state) => state.messages)
  const { refresh, send, stop } = useMessagesActions()
  const { streamingActive, liveActiveAgent, liveTool, liveAgents, turnStats } = useStreamingState()
  const currentId = useCurrentThread()
  const displaySettings = useDisplaySettings()
  const { mode, streaming } = useAppMode()
  const token = useAuthToken()

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
  const [input, setInput] = useState('')
  const msgsRef = useRef<HTMLDivElement | null>(null)

  const shouldStickRef = useRef(true)
  useEffect(() => {
    const el = msgsRef.current
    if (!el) return
    const onScroll = () => {
      const nearBottom =
        el.scrollTop + el.clientHeight >= el.scrollHeight - SCROLL_STICKY_THRESHOLD_PX
      shouldStickRef.current = nearBottom
    }
    el.addEventListener('scroll', onScroll)
    return () => el.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    if (currentId) refresh(currentId)
  }, [currentId, refresh])
  useEffect(() => {
    useMessages.setState({ turnStats: null })
  }, [currentId])
  useEffect(() => {
    const el = msgsRef.current
    if (!el) return
    if (shouldStickRef.current) el.scrollTop = el.scrollHeight
  }, [messages])
  useEffect(() => {
    if (mode === 'developer') {
      useSettings.setState({ showMeta: true, showTimestamps: true })
    }
  }, [mode])
  // Global keyboard shortcuts
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
          useThreads.getState().createThread()
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

  return (
    <main className="flex-1 flex flex-col bg-[rgba(10,14,26,0.3)]" aria-busy={streamingActive}>
      <div className="flex items-center gap-[var(--space-3)] px-[var(--space-5)] py-[var(--space-4)] border-b border-border bg-[rgba(17,24,39,0.9)] backdrop-blur-3xl shadow-[0_4px_16px_rgba(0,0,0,0.5)] justify-between">
        <div className="flex gap-[var(--space-2)] items-center flex-wrap">
          <strong>Thread</strong>
          <span>#{currentId ?? '-'}</span>
          {streamingActive ? (
            <span
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-accent/20 text-accent border border-accent/30"
              title="Model is streaming a reply"
            >
              <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
              Streaming…
            </span>
          ) : null}
          {streamingActive && liveActiveAgent ? (
            <span
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-purple-500/20 text-purple-400 border border-purple-500/30"
              title="Active agent"
            >
              Agent: {liveActiveAgent}
            </span>
          ) : null}
          {streamingActive && Array.isArray(liveAgents) && liveAgents.length ? (
            <span
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
              title={`Agents: ${liveAgents.join(', ')}`}
            >
              agents {liveAgents.length}
            </span>
          ) : null}
          {streamingActive && liveTool ? (
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${liveTool.status === 'running' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'bg-green-500/20 text-green-400 border border-green-500/30'}`}
              title={liveTool.status === 'running' ? 'Tool running' : 'Tool finished'}
            >
              {liveTool.status === 'running' ? (
                <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : null}
              Tool: {liveTool.name} {liveTool.status === 'running' ? '(running…) ' : '(done)'}
            </span>
          ) : null}
          {!streamingActive && turnStats ? (
            <>
              {!!(turnStats.model && turnStats.model.length > 0) ||
              !!(
                turnStats.provider &&
                (turnStats.token_in != null ||
                  turnStats.token_out != null ||
                  turnStats.cost_usd != null)
              ) ? (
                <span
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
                  title="Model used"
                >
                  {turnStats.provider
                    ? `${turnStats.provider}${turnStats.model ? ':' + turnStats.model : ''}`
                    : turnStats.model || ''}
                </span>
              ) : null}
              {turnStats.token_in != null || turnStats.token_out != null ? (
                <span
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
                  title="Prompt/Completion tokens"
                >
                  tokens {turnStats.token_in ?? 0}/{turnStats.token_out ?? 0}
                </span>
              ) : null}
              {turnStats.cost_usd != null ? (
                <span
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
                  title="Estimated cost"
                >
                  ${String(turnStats.cost_usd)}
                </span>
              ) : null}
              {turnStats.api_calls != null ? (
                <span
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
                  title="API calls"
                >
                  calls {turnStats.api_calls}
                </span>
              ) : null}
              {Array.isArray(turnStats.agents) && turnStats.agents.length ? (
                <span
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
                  title={`Agents: ${turnStats.agents.join(', ')}`}
                >
                  agents {turnStats.agents.length}
                </span>
              ) : null}
              {Array.isArray(turnStats.tools) && turnStats.tools.length ? (
                <span
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
                  title={`Tools: ${turnStats.tools.join(', ')}`}
                >
                  tools {turnStats.tools.length}
                </span>
              ) : null}
            </>
          ) : null}
        </div>
        <div className="flex gap-2 items-center">
          {currentId && <SummaryIndicator threadId={currentId} />}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => useHelp.getState().openHelp()}
            aria-label="Open keyboard shortcuts"
          >
            Help
          </Button>
          {streamingActive ? (
            <Button variant="ghost" size="sm" onClick={stop} aria-label="Stop streaming">
              Stop
            </Button>
          ) : null}
          <AuthControls />
          <SettingsButton />
          <HeaderOverflowMenu
            actions={useMemo<HeaderMenuAction[]>(
              () => [
                {
                  label: 'Rename',
                  onClick: () => {
                    if (!currentId) return
                    const t =
                      useThreads.getState().threads.find((x) => x.id === currentId)?.title ||
                      `Thread #${currentId}`
                    usePrompt.getState().openPrompt({
                      title: 'Rename thread',
                      defaultValue: t,
                      confirmText: 'Rename',
                      onSubmit: async (name) => {
                        if (!name.trim()) return
                        await useThreads.getState().renameThread(currentId, name)
                        useToasts.getState().push({ type: 'success', text: 'Thread renamed' })
                      },
                    })
                  },
                  disabled: !currentId || streamingActive,
                },
                {
                  label: 'Delete',
                  onClick: () => {
                    if (!currentId) return
                    const t =
                      useThreads.getState().threads.find((x) => x.id === currentId)?.title ||
                      `Thread #${currentId}`
                    useConfirm.getState().openConfirm({
                      title: 'Delete thread?',
                      description: `"${t}" will be permanently removed.`,
                      confirmText: 'Delete',
                      onConfirm: async () => {
                        await useThreads.getState().deleteThread(currentId)
                        useToasts.getState().push({ type: 'success', text: 'Thread deleted' })
                      },
                    })
                  },
                  disabled: !currentId || streamingActive,
                },
                {
                  label: 'Toggle Theme',
                  onClick: () =>
                    useSettings.setState((s) => ({ theme: s.theme === 'dark' ? 'light' : 'dark' })),
                },
                {
                  label: 'Export',
                  onClick: async () => {
                    if (!currentId) return
                    const { ok, data } = await api(`/api/threads/${currentId}/export`)
                    if (ok && data) {
                      const blob = new Blob([JSON.stringify(data, null, 2)], {
                        type: 'application/json',
                      })
                      const a = document.createElement('a')
                      a.href = URL.createObjectURL(blob)
                      a.download = `thread-${currentId}.json`
                      a.click()
                      useToasts.getState().push({ type: 'success', text: 'Exported thread JSON' })
                    } else {
                      useToasts.getState().push({ type: 'error', text: 'Export failed' })
                    }
                  },
                  disabled: !currentId || streamingActive,
                },
                {
                  label: 'Import',
                  onClick: () => {
                    const input = document.querySelector<HTMLInputElement>(
                      'input[aria-label="Import thread file"]'
                    )
                    if (input && !input.disabled) input.click()
                  },
                  disabled: streamingActive,
                },
              ],
              [currentId, streamingActive]
            )}
          />
        </div>
      </div>
      <div
        className="flex-1 overflow-auto p-[var(--space-6)] flex flex-col gap-[var(--space-4)] scroll-smooth"
        ref={msgsRef}
        role="log"
        aria-live="polite"
        aria-relevant="additions text"
        aria-label="Chat messages"
      >
        {currentId ? (
          messages.length ? (
            messages.map((m) => (
              <MessageView
                key={m.id + ':' + m.created_at}
                m={m}
                showModel={displaySettings.showModel}
                showTimestamps={displaySettings.showTimestamps}
                showMeta={displaySettings.showMeta}
                allMessages={messages}
              />
            ))
          ) : (
            <div className="text-center py-12 px-6 text-muted text-base">
              No messages yet. Say hello!
            </div>
          )
        ) : (
          <div className="text-center py-12 px-6 text-muted text-base">
            Select or create a thread to begin.
          </div>
        )}
      </div>
      <div className="flex gap-[var(--space-3)] px-[var(--space-5)] py-[var(--space-4)] border-t border-border bg-[rgba(17,24,39,0.9)] backdrop-blur-3xl shadow-[0_-4px_16px_rgba(0,0,0,0.5)]">
        <textarea
          className="composer"
          rows={2}
          style={{ flex: 1 }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={streamingActive}
          onKeyDown={(e) => {
            if (!streamingActive && e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              if (currentId && input.trim()) {
                send(currentId, input.trim(), 'user', streaming === 'sse')
                setInput('')
              }
            } else if (!streamingActive && e.key === 'ArrowUp' && !input.trim()) {
              const lastUser = [...messages].reverse().find((m) => m.role === 'user')
              if (lastUser) {
                e.preventDefault()
                usePrompt.getState().openPrompt({
                  title: 'Edit last message',
                  defaultValue: lastUser.content,
                  textarea: true,
                  confirmText: 'Save',
                  onSubmit: async (content) => {
                    await useMessages.getState().edit(lastUser.id, content)
                    if (currentId) await refresh(currentId)
                  },
                })
              }
            }
          }}
          aria-label="Message input"
          placeholder="Type a message..."
        />
        {!streamingActive ? (
          <Button
            onClick={() => {
              if (currentId && input.trim()) {
                send(currentId, input.trim(), 'user', streaming === 'sse')
                setInput('')
              }
            }}
            disabled={!currentId}
            aria-label="Send message"
          >
            Send
          </Button>
        ) : (
          <Button variant="destructive" onClick={stop} aria-label="Stop streaming">
            Stop
          </Button>
        )}
      </div>
      <label style={{ display: 'none' }} aria-label="Import thread from JSON">
        <input
          type="file"
          aria-label="Import thread file"
          onChange={async (e) => {
            const f = e.currentTarget.files?.[0]
            if (!f) return
            const text = await f.text()
            try {
              const obj = JSON.parse(text)
              const res = await api('/api/threads/import', { method: 'POST', json: obj })
              if (res.ok && (res.data as any)?.id) {
                await useThreads.getState().refresh()
                useThreads.getState().setCurrent((res.data as any).id)
                useToasts.getState().push({
                  type: 'success',
                  text: `Imported to thread #${(res.data as any).id}`,
                })
              } else {
                useToasts.getState().push({ type: 'error', text: 'Import failed' })
              }
            } catch {
              useToasts.getState().push({ type: 'error', text: 'Invalid JSON file' })
            }
            ;(e.currentTarget as HTMLInputElement).value = ''
          }}
          disabled={streamingActive as any}
        />
      </label>
    </main>
  )
}
