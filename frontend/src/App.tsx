import React, { useEffect, useRef, useState, lazy, Suspense } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { create } from 'zustand'
import { useSpring, animated } from '@react-spring/web'
const SettingsModal = lazy(() =>
  import('./components/SettingsModal').then((m) => ({ default: m.SettingsModal }))
)
import { MetadataTooltip } from './components/MetadataTooltip'
import { ThinkingTokens } from './components/ThinkingTokens'
const PriceChart = lazy(() =>
  import('./components/PriceChart').then((m) => ({ default: m.PriceChart }))
)
import { AgentBadgeGroup } from './components/AgentBadge'
import { BranchNavigator } from './components/BranchNavigator'
import { SummaryIndicator } from './components/SummaryIndicator'
import { api } from './lib/apiClient'
import { Button } from './components/ui/button'
import { Input } from './components/ui/input'
import { Textarea } from './components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './components/ui/dialog'
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
} from './components/ui/alert-dialog'
import { PricesPanel } from './components/PricesPanel'

// --- Toasts (imported from toastStore.ts)
import { useToasts } from './stores/toastStore'

function Toasts() {
  const { toasts, remove } = useToasts()
  useEffect(() => {
    const timers = toasts.map((t) => setTimeout(() => remove(t.id), 4000))
    return () => {
      timers.forEach(clearTimeout)
    }
  }, [toasts, remove])
  return (
    <div
      className="fixed right-5 bottom-5 flex flex-col gap-3 z-50"
      aria-live="polite"
      role="status"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`backdrop-blur-2xl bg-panel-solid border rounded-xl px-4 py-3 shadow-lg max-w-[380px] animate-slideInRight text-sm font-medium ${t.type === 'info' ? 'border-blue-500 bg-gradient-to-br from-blue-500/15 to-panel-solid' : t.type === 'success' ? 'border-green-500 bg-gradient-to-br from-green-500/15 to-panel-solid' : 'border-red-500 bg-gradient-to-br from-red-500/15 to-panel-solid'}`}
          onClick={() => remove(t.id)}
          title="Click to dismiss"
        >
          {t.text}
        </div>
      ))}
    </div>
  )
}

// --- Prompt modal
type PromptOpts = {
  title: string
  defaultValue?: string
  textarea?: boolean
  confirmText?: string
  onSubmit: (value: string) => void | Promise<void>
}

const usePrompt = create<{
  open: boolean
  title: string
  value: string
  textarea: boolean
  confirmText: string
  submitting: boolean
  onSubmit: ((v: string) => void | Promise<void>) | null
  openPrompt: (opts: PromptOpts) => void
  close: () => void
}>((set) => ({
  open: false,
  title: '',
  value: '',
  textarea: false,
  confirmText: 'OK',
  submitting: false,
  onSubmit: null,
  openPrompt: (opts) =>
    set({
      open: true,
      title: opts.title,
      value: opts.defaultValue || '',
      textarea: !!opts.textarea,
      confirmText: opts.confirmText || 'OK',
      onSubmit: opts.onSubmit || null,
      submitting: false,
    }),
  close: () => set({ open: false, submitting: false }),
}))

function PromptModal() {
  const { open, title, value, textarea, confirmText, submitting, onSubmit } = usePrompt()
  const setState = usePrompt.setState
  const inputRef = useRef<HTMLTextAreaElement | HTMLInputElement | null>(null)

  useEffect(() => {
    if (open && inputRef.current) {
      setTimeout(() => {
        const input = inputRef.current
        if (input) {
          input.focus()
          if ('select' in input) {
            try {
              ;(input as any).select()
            } catch {
              /* ignore */
            }
          }
        }
      }, 0)
    }
  }, [open])

  const handleConfirm = async () => {
    if (!onSubmit) return usePrompt.getState().close()
    setState({ submitting: true })
    try {
      await onSubmit(value)
      usePrompt.getState().close()
    } catch (e: any) {
      useToasts.getState().push({ type: 'error', text: e?.message || 'Action failed' })
      setState({ submitting: false })
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => !isOpen && !submitting && usePrompt.getState().close()}
    >
      <DialogContent className="sm:max-w-[640px]">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          {textarea ? (
            <Textarea
              ref={inputRef as any}
              rows={6}
              value={value}
              onChange={(e) => setState({ value: e.target.value })}
              disabled={submitting}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.ctrlKey && !submitting) {
                  e.preventDefault()
                  handleConfirm()
                }
              }}
            />
          ) : (
            <Input
              ref={inputRef as any}
              value={value}
              onChange={(e) => setState({ value: e.target.value })}
              disabled={submitting}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !submitting) {
                  e.preventDefault()
                  handleConfirm()
                }
              }}
            />
          )}
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => usePrompt.getState().close()}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button onClick={handleConfirm} disabled={submitting || !value.trim()}>
            {confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// --- Confirm modal
export type ConfirmOpts = {
  title?: string
  description?: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void | Promise<void>
}
const useConfirm = create<{
  open: boolean
  title: string
  description: string
  confirmText: string
  cancelText: string
  busy: boolean
  onConfirm: (() => void | Promise<void>) | null
  openConfirm: (opts: ConfirmOpts) => void
  close: () => void
}>((set) => ({
  open: false,
  title: 'Are you sure?',
  description: 'This action cannot be undone.',
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  busy: false,
  onConfirm: null,
  openConfirm: (opts) =>
    set({
      open: true,
      title: opts.title || 'Are you sure?',
      description: opts.description || 'This action cannot be undone.',
      confirmText: opts.confirmText || 'Confirm',
      cancelText: opts.cancelText || 'Cancel',
      onConfirm: opts.onConfirm,
      busy: false,
    }),
  close: () => set({ open: false, busy: false }),
}))

function ConfirmModal() {
  const { open, title, description, confirmText, cancelText, busy, onConfirm } = useConfirm()
  const setState = useConfirm.setState

  const handleConfirm = async () => {
    if (!onConfirm) return useConfirm.getState().close()
    setState({ busy: true })
    try {
      await onConfirm()
      useConfirm.getState().close()
    } catch (e: any) {
      useToasts.getState().push({ type: 'error', text: e?.message || 'Action failed' })
      setState({ busy: false })
    }
  }

  return (
    <AlertDialog
      open={open}
      onOpenChange={(isOpen) => !isOpen && !busy && useConfirm.getState().close()}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={busy}>{cancelText}</AlertDialogCancel>
          <AlertDialogAction onClick={handleConfirm} disabled={busy}>
            {confirmText}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

// --- Help modal
const useHelp = create<{ open: boolean; openHelp: () => void; close: () => void }>((set) => ({
  open: false,
  openHelp: () => set({ open: true }),
  close: () => set({ open: false }),
}))

function HelpModal() {
  const { open } = useHelp()

  const Row = ({ k, d }: { k: string; d: string }) => (
    <div className="flex justify-between gap-3">
      <code className="opacity-90">{k}</code>
      <span className="opacity-85">{d}</span>
    </div>
  )

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && useHelp.getState().close()}>
      <DialogContent className="sm:max-w-[640px]">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
        </DialogHeader>
        <div className="grid gap-2 max-h-[400px] overflow-y-auto py-4">
          <div className="font-semibold mt-2 opacity-90">General</div>
          <Row k="Ctrl+/" d="Open this help" />
          <Row k="Ctrl+," d="Open settings" />
          <Row k="Ctrl+L" d="Toggle theme" />
          <Row k="Ctrl+B" d="Toggle sidebar" />
          <div className="font-semibold mt-2 opacity-90">Threads</div>
          <Row k="Ctrl+N" d="New thread" />
          <Row k="Ctrl+Shift+E" d="Export thread" />
          <Row k="Ctrl+Shift+I" d="Import thread" />
          <div className="font-semibold mt-2 opacity-90">Messaging</div>
          <Row k="Ctrl+K" d="Focus composer" />
          <Row k="Ctrl+Shift+K" d="Clear composer" />
          <Row k="Ctrl+Enter" d="Send message" />
          <Row k="Escape" d="Stop streaming" />
          <Row k="Up Arrow (empty input)" d="Edit last message" />
          <div className="font-semibold mt-2 opacity-90">Message Actions</div>
          <Row k="Hover + C / Ctrl+C" d="Copy message" />
          <Row k="Hover + E" d="Edit (user msgs)" />
          <Row k="Hover + Delete" d="Delete message" />
        </div>
        <DialogFooter>
          <Button onClick={() => useHelp.getState().close()}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// --- Auth store (imported from authStore.ts)
import { useAuth } from './stores/authStore'

// --- Settings store (imported from settingsStore.ts)
import { useSettings, type Settings } from './stores/settingsStore'

// --- Threads store (imported from threadStore.ts)
import { useThreads } from './stores/threadStore'

// --- Messages store (imported from messageStore.ts)
import { useMessages, type Message } from './stores/messageStore'

// --- UI Components
function Sidebar() {
  const { threads, currentId, setCurrent, refresh, createDraftThread } = useThreads()
  const [collapsed, setCollapsed] = useState(localStorage.getItem('sidebarCollapsed') === '1')
  const auth = useAuth()

  useEffect(() => {
    refresh().then(() => {
      const last = Number(localStorage.getItem('lastThreadId') || '')
      if (last) setCurrent(last)
    })
  }, [refresh, setCurrent])

  useEffect(() => {
    document.querySelector('.sidebar')?.classList.toggle('collapsed', collapsed)
  }, [collapsed])

  const handleLogout = async () => {
    useConfirm.getState().openConfirm({
      title: 'Sign out?',
      description: 'You will need to sign in again to access the chat.',
      confirmText: 'Sign Out',
      onConfirm: async () => {
        try {
          await auth.logout()
        } catch {
          /* ignore */
        }
        window.location.href = '/auth'
      },
    })
  }

  return (
    <aside
      className={`${collapsed ? 'w-14' : 'w-[280px]'} border-r border-border p-4 overflow-auto bg-white/90 text-slate-900 shadow-[0_12px_32px_rgba(15,23,42,0.12)] dark:bg-[rgba(17,24,39,0.85)] dark:text-white dark:shadow-none backdrop-blur-3xl transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]`}
      aria-label="Threads sidebar"
    >
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          <Button
            variant="ghost"
            size="icon"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            onClick={() =>
              setCollapsed((c) => {
                const n = !c
                localStorage.setItem('sidebarCollapsed', n ? '1' : '0')
                return n
              })
            }
            aria-expanded={!collapsed}
            aria-controls="thread-list"
          >
            {collapsed ? '⮞' : '⮜'}
          </Button>
          <Button
            onClick={() => createDraftThread()}
            aria-label="Create new thread"
            style={{ flex: 1 }}
          >
            + New Chat
          </Button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', marginBottom: 16 }}>
          <ul id="thread-list" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
            {threads.map((t) => (
              <li
                key={t.id}
                style={{
                  padding: '10px 12px',
                  borderRadius: '12px',
                  background: currentId === t.id ? 'var(--accent-color)' : 'transparent',
                  cursor: 'pointer',
                  marginBottom: '6px',
                  transition: 'all 0.2s ease',
                  color: currentId === t.id ? 'white' : 'var(--fg)',
                  fontWeight: currentId === t.id ? 500 : 400,
                  border: '1px solid',
                  borderColor: currentId === t.id ? 'transparent' : 'transparent',
                }}
                onClick={() => setCurrent(t.id)}
                aria-current={currentId === t.id ? 'true' : undefined}
                onMouseEnter={(e) => {
                  if (currentId !== t.id) {
                    e.currentTarget.style.background = 'var(--accent-light)'
                    e.currentTarget.style.borderColor = 'var(--border-color)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (currentId !== t.id) {
                    e.currentTarget.style.background = 'transparent'
                    e.currentTarget.style.borderColor = 'transparent'
                  }
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 8,
                  }}
                >
                  <span
                    style={{
                      flex: 1,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {t.title || `Thread #${t.id}`}
                  </span>
                  <span onClick={(e) => e.stopPropagation()}>
                    <SummaryIndicator threadId={t.id} />
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div
          style={{
            borderTop: '1px solid var(--border-color)',
            paddingTop: 12,
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          <Button
            variant="outline"
            onClick={() => useSettings.getState().setSettingsOpen(true)}
            className="flex items-center gap-2"
            aria-label="Open settings"
          >
            <span>⚙️</span>
            <span>Settings</span>
          </Button>

          {auth.user && (
            <div
              style={{
                padding: '10px 12px',
                background: 'var(--panel)',
                border: '1px solid var(--border-color)',
                borderRadius: '12px',
                fontSize: '13px',
              }}
            >
              <div style={{ opacity: 0.7, marginBottom: 4 }}>Signed in as</div>
              <div
                style={{
                  fontWeight: 500,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {auth.user.full_name || auth.user.email}
              </div>
            </div>
          )}

          <Button
            variant="destructive"
            onClick={handleLogout}
            className="flex items-center gap-2"
            aria-label="Sign out"
          >
            <span>🚪</span>
            <span>Sign Out</span>
          </Button>
        </div>
      </div>
    </aside>
  )
}

function MessageView({
  m,
  showModel,
  showTimestamps,
  showMeta,
  allMessages,
}: {
  m: Message
  showModel: boolean
  showTimestamps: boolean
  showMeta: boolean
  allMessages: Message[]
}) {
  const { del, refresh, streamingActive } = useMessages()
  const { currentId } = useThreads()
  const { showThinking } = useSettings()

  const handleNavigate = async (targetMessageId: number) => {
    // Scroll to the target message
    const targetEl = document.querySelector(`[data-message-id="${targetMessageId}"]`)
    if (targetEl) {
      targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // Highlight briefly
      targetEl.classList.add('highlight-pulse')
      setTimeout(() => targetEl.classList.remove('highlight-pulse'), 2000)
    }
  }

  const [hovered, setHovered] = useState(false)

  const fadeIn = useSpring({
    from: { opacity: 0, transform: 'translateY(20px) scale(0.95)' },
    to: { opacity: 1, transform: 'translateY(0px) scale(1)' },
    config: { tension: 280, friction: 60 },
  })

  const hoverSpring = useSpring({
    backgroundColor: hovered ? 'var(--hover-bg)' : 'transparent',
    config: { tension: 300, friction: 30 },
  })

  const rowRef = useRef<HTMLDivElement | null>(null)
  useEffect(() => {
    const el = rowRef.current
    if (!el) return
    const onKey = (e: KeyboardEvent) => {
      if (streamingActive) return
      if (document.activeElement && (document.activeElement as HTMLElement).tagName === 'TEXTAREA')
        return
      if (!el.matches(':hover')) return
      if (e.key === 'c' || (e.ctrlKey && e.key.toLowerCase() === 'c')) {
        navigator.clipboard.writeText(m.content || '')
      } else if (e.key.toLowerCase() === 'e' && m.role === 'user') {
        usePrompt.getState().openPrompt({
          title: 'Edit message',
          defaultValue: m.content,
          textarea: true,
          confirmText: 'Save',
          onSubmit: async (content) => {
            await useMessages.getState().edit(m.id, content)
            if (currentId) await refresh(currentId)
          },
        })
      } else if (e.key === 'Delete') {
        useConfirm.getState().openConfirm({
          title: 'Delete message?',
          description: 'This message will be permanently removed.',
          confirmText: 'Delete',
          onConfirm: async () => {
            await del(m.id)
            if (currentId) await refresh(currentId)
            useToasts.getState().push({ type: 'success', text: 'Message deleted' })
          },
        })
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [m.id, m.content, m.role, streamingActive, currentId, refresh, del])

  const agentNames = m.agents?.activated || []
  const { liveActiveAgent, liveTool } = useMessages()

  const bubbleBase =
    'border rounded-2xl px-5 py-4 whitespace-pre-wrap transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] leading-[1.7] relative'
  const userBubble =
    'bg-gradient-to-br from-indigo-500 to-purple-600 text-white border-0 shadow-[0_16px_32px_rgba(76,81,191,0.35)]'
  const assistantBubble =
    'bg-white/90 text-slate-900 border-slate-200 shadow-[0_16px_40px_rgba(15,23,42,0.14)] dark:bg-gradient-to-br dark:from-slate-800/70 dark:to-slate-900/80 dark:text-white dark:border-indigo-500/20 dark:shadow-[0_4px_12px_rgba(0,0,0,0.4)] dark:backdrop-blur-3xl'

  return (
    <animated.div
      ref={rowRef}
      className="max-w-[900px] animate-slideIn origin-left"
      role="article"
      aria-label={`${m.role} message`}
      style={{ ...fadeIn, ...hoverSpring }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      data-message-id={m.id}
    >
      {agentNames.length ? (
        <div style={{ marginBottom: 8 }}>
          <AgentBadgeGroup agents={agentNames} activeAgent={liveActiveAgent} variant="pill" />
        </div>
      ) : null}
      {m.id === -1 ? (
        <div
          className="mt-2 opacity-70 text-xs flex gap-2 flex-wrap mb-1"
          style={{ marginBottom: 4 }}
        >
          {liveActiveAgent ? (
            <span className="text-xs opacity-95 border border-accent px-3 py-1 rounded-xl bg-gradient-to-br from-accent-light to-purple-500/15 text-accent font-medium transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] shadow-[0_2px_4px_rgba(99,102,241,0.1)]">
              Agent: {liveActiveAgent}
            </span>
          ) : null}
          {liveTool ? (
            <span
              className={`text-xs opacity-95 border border-accent px-3 py-1 rounded-xl bg-gradient-to-br from-accent-light to-purple-500/15 text-accent font-medium transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] shadow-[0_2px_4px_rgba(99,102,241,0.1)] ${liveTool.status === 'done' ? 'opacity-70' : ''}`}
            >
              {liveTool.status === 'running' ? (
                <span className="inline-block w-3.5 h-3.5 border-2 border-accent-light border-t-accent rounded-full animate-spin mr-1.5" />
              ) : null}
              Tool: {liveTool.name} {liveTool.status === 'running' ? '(running…) ' : '(done)'}
            </span>
          ) : null}
        </div>
      ) : null}
       <div className={`${bubbleBase} ${m.role === 'user' ? userBubble : assistantBubble}`}>
         {m.role === 'assistant' ? (
           <div className="prose max-w-none dark:prose-invert prose-p:my-1 prose-li:my-0.5 prose-ul:my-1 prose-ol:my-1">
             <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content || ''}</ReactMarkdown>
           </div>
         ) : (
           m.content
         )}
       </div>
      {showThinking && m.thinking && m.role === 'assistant' ? (
        <ThinkingTokens thinking={m.thinking} />
      ) : null}
      {m.metadata?.priceData && m.role === 'assistant' ? (
        <div style={{ marginTop: 12 }}>
          <Suspense fallback={<div className="chart-loading">Loading chart…</div>}>
            <PriceChart
              data={m.metadata.priceData}
              sku={m.metadata.sku || 'Product'}
              theme={useSettings.getState().theme}
            />
          </Suspense>
        </div>
      ) : null}
      {m.id > 0 && allMessages.length > 0 ? (
        <BranchNavigator message={m} allMessages={allMessages} onNavigate={handleNavigate} />
      ) : null}
      <div className="flex gap-1.5 mt-2 opacity-0 transition-opacity duration-200 hover:opacity-100">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigator.clipboard.writeText(m.content || '')}
          disabled={streamingActive}
          aria-label="Copy message"
        >
          Copy
        </Button>
        {m.role === 'user' ? <EditButton m={m} /> : null}
        <Button
          variant="ghost"
          size="sm"
          onClick={async () => {
            useConfirm.getState().openConfirm({
              title: 'Delete message?',
              description: 'This message will be permanently removed.',
              confirmText: 'Delete',
              onConfirm: async () => {
                await del(m.id)
                if (currentId) await refresh(currentId)
                useToasts.getState().push({ type: 'success', text: 'Message deleted' })
              },
            })
          }}
          disabled={streamingActive}
          aria-label="Delete message"
        >
          Del
        </Button>
        <BranchButtons m={m} />
      </div>
      <div className="mt-2 opacity-70 text-xs flex gap-2 flex-wrap">
        {showTimestamps && m.created_at ? (
          <span className="time" title={m.created_at}>
            {new Date(m.created_at).toLocaleString()}
          </span>
        ) : null}
        {showMeta ? <MetadataTooltip message={m} /> : null}
        {m.role === 'assistant' &&
        showModel &&
        ((m.model && m.model.length > 0) ||
          (m.metadata?.provider &&
            (m.token_in != null || m.token_out != null || m.cost_usd != null))) ? (
          <span className="opacity-60 text-[11px] ml-auto" title={m.model || ''}>
            {m.metadata?.provider
              ? `${m.metadata.provider}${m.model ? ':' + m.model : ''}`
              : m.model}
          </span>
        ) : null}
      </div>
    </animated.div>
  )
}

function EditButton({ m }: { m: Message }) {
  const { edit, refresh, streamingActive } = useMessages()
  const { currentId } = useThreads()
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={async () => {
        usePrompt.getState().openPrompt({
          title: 'Edit message',
          defaultValue: m.content,
          textarea: true,
          confirmText: 'Save',
          onSubmit: async (content) => {
            await edit(m.id, content)
            if (currentId) await refresh(currentId)
          },
        })
      }}
      disabled={streamingActive}
      aria-label="Edit message"
    >
      Edit
    </Button>
  )
}

function BranchButtons({ m }: { m: Message }) {
  const { branch, fork, refresh, streamingActive } = useMessages()
  const { currentId } = useThreads()
  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={async () => {
          if (!currentId) return
          usePrompt.getState().openPrompt({
            title: 'Branch here. Your message:',
            defaultValue: '',
            textarea: true,
            confirmText: 'Branch',
            onSubmit: async (content) => {
              if (!content.trim()) return
              await branch(currentId, m.id, content, 'user')
              await refresh(currentId)
            },
          })
        }}
        disabled={streamingActive}
        aria-label="Branch conversation here"
      >
        Branch
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={async () => {
          if (!currentId) return
          usePrompt.getState().openPrompt({
            title: 'Fork thread title',
            defaultValue: `Fork of #${currentId} at message ${m.id}`,
            textarea: false,
            confirmText: 'Fork',
            onSubmit: async (title) => {
              if (!title.trim()) return
              const newId = await fork(currentId, m, title)
              if (newId) {
                useThreads.getState().setCurrent(newId)
                await useThreads.getState().refresh()
                useToasts.getState().push({ type: 'success', text: `Forked to thread #${newId}` })
              }
            },
          })
        }}
        disabled={streamingActive}
        aria-label="Fork new thread from here"
      >
        Fork
      </Button>
    </>
  )
}

function AuthControls() {
  const auth = useAuth()
  const { token, user, fetchMe } = auth
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (token && !user) fetchMe().catch(() => {})
  }, [token, user, fetchMe])

  if (token) {
    return (
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <span style={{ opacity: 0.8 }}>
          Signed in as {auth.user?.full_name || auth.user?.email || 'user'}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => auth.logout()}
          disabled={busy}
          aria-label="Logout"
        >
          Logout
        </Button>
      </div>
    )
  }

  return (
    <details>
      <summary>Auth</summary>
      <div style={{ display: 'grid', gridTemplateColumns: 'auto auto', gap: 8, paddingTop: 8 }}>
        <input
          placeholder="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value)
            setError(null)
          }}
        />
        <input
          placeholder="password"
          type="password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value)
            setError(null)
          }}
        />
        <input
          placeholder="username (opt)"
          value={username}
          onChange={(e) => {
            setUsername(e.target.value)
            setError(null)
          }}
        />
        <div style={{ display: 'flex', gap: 8 }}>
          <Button
            size="sm"
            onClick={async () => {
              setBusy(true)
              setError(null)
              try {
                const r = await auth.login(email, password)
                if (!r.ok) setError(r.error || 'Login failed')
              } finally {
                setBusy(false)
              }
            }}
            disabled={busy || !email || !password}
            aria-label="Login"
          >
            Login
          </Button>
          <Button
            size="sm"
            onClick={async () => {
              setBusy(true)
              setError(null)
              try {
                const r = await auth.register(email, password, username || undefined)
                if (!r.ok) setError(r.error || 'Register failed')
              } finally {
                setBusy(false)
              }
            }}
            disabled={busy || !email || !password}
            aria-label="Register"
          >
            Register
          </Button>
        </div>
        {error ? (
          <div style={{ gridColumn: '1 / -1', color: 'tomato', fontSize: 12 }}>{error}</div>
        ) : null}
      </div>
    </details>
  )
}

function ChatPane() {
  const {
    messages,
    refresh,
    send,
    streamingActive,
    stop,
    liveActiveAgent,
    liveTool,
    liveAgents,
    turnStats,
  } = useMessages()
  const { currentId } = useThreads()
  const settings = useSettings()
  const auth = useAuth()

  useEffect(() => {
    ;(async () => {
      const t = auth.token || localStorage.getItem('token') || ''
      const url = t ? `/api/settings?token=${encodeURIComponent(t)}` : '/api/settings'
      const { ok, data } = await api(url)
      if (ok && data?.settings) {
        useSettings.setState((s) => ({
          ...s,
          showThinking: !!data.settings.show_thinking,
          showTimestamps: !!data.settings.show_timestamps,
          showModel: !!data.settings.show_model_tag,
          showMeta: !!data.settings.show_metadata_panel,
          theme: data.settings.theme || s.theme,
          streaming: data.settings.streaming || s.streaming,
          mode: data.settings.mode || s.mode,
        }))
      }
    })()
  }, [auth.token])
  const [input, setInput] = useState('')
  const msgsRef = useRef<HTMLDivElement | null>(null)

  // near-bottom autoscroll: only when user hasn't scrolled far up
  const shouldStickRef = useRef(true)
  useEffect(() => {
    const el = msgsRef.current
    if (!el) return
    const onScroll = () => {
      const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 48
      shouldStickRef.current = nearBottom
    }
    el.addEventListener('scroll', onScroll)
    return () => el.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    if (currentId) refresh(currentId)
  }, [currentId, refresh])
  // Clear header turnStats when switching threads
  useEffect(() => {
    useMessages.setState({ turnStats: null })
  }, [currentId])
  useEffect(() => {
    const el = msgsRef.current
    if (!el) return
    if (shouldStickRef.current) el.scrollTop = el.scrollHeight
  }, [messages])
  // Developer mode: auto-enable info & timestamps locally
  useEffect(() => {
    if (settings.mode === 'developer') {
      useSettings.setState({ showMeta: true, showTimestamps: true })
    }
  }, [settings.mode])
  // Global keyboard shortcuts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const composer = document.querySelector<HTMLTextAreaElement>('.composer textarea')
      // Escape to stop streaming
      if (e.key === 'Escape' && streamingActive) {
        stop()
        return
      }
      // Avoid when focused inside inputs except Ctrl+/ and Escape
      const tag = (document.activeElement as HTMLElement | null)?.tagName || ''
      const inInput =
        tag === 'INPUT' ||
        tag === 'TEXTAREA' ||
        (document.activeElement as HTMLElement | null)?.isContentEditable
      // Ctrl+/ help
      if (e.ctrlKey && e.key === '/') {
        e.preventDefault()
        useHelp.getState().openHelp()
        return
      }
      // Ctrl+B toggle sidebar
      if (e.ctrlKey && e.key.toLowerCase() === 'b') {
        e.preventDefault()
        const btn = document.querySelector<HTMLButtonElement>(
          '.sidebar button[aria-label*="sidebar"]'
        )
        btn?.click()
        return
      }
      // Ctrl+N new thread
      if (e.ctrlKey && e.key.toLowerCase() === 'n') {
        e.preventDefault()
        useThreads.getState().createDraftThread()
        return
      }
      if (inInput) {
        // Allow Ctrl+Enter to send and Ctrl+Shift+K to clear while in composer
        if (composer && document.activeElement === composer) {
          if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault()
            if (!settings || streamingActive) return
            const value = composer.value.trim()
            if (currentId && value) {
              send(currentId, value, 'user', settings.streaming === 'sse')
              composer.value = ''
              ;(composer as any).dispatchEvent(new Event('input', { bubbles: true }))
              setInput('')
            }
            return
          }
          if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'k') {
            e.preventDefault()
            composer.value = ''
            ;(composer as any).dispatchEvent(new Event('input', { bubbles: true }))
            setInput('')
            return
          }
        }
        return
      }
      // Ctrl+K focus composer
      if (e.ctrlKey && e.key.toLowerCase() === 'k' && !e.shiftKey) {
        e.preventDefault()
        composer?.focus()
        return
      }
      // Ctrl+L toggle theme
      if (e.ctrlKey && e.key.toLowerCase() === 'l') {
        e.preventDefault()
        useSettings.setState((s) => ({ theme: s.theme === 'dark' ? 'light' : 'dark' }))
        return
      }
      // Ctrl+Shift+E export thread
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'e') {
        e.preventDefault()
        const btn = document.querySelector<HTMLButtonElement>('button[aria-label="Export thread"]')
        if (btn && !btn.disabled) btn.click()
        return
      }
      // Ctrl+Shift+I import thread
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'i') {
        e.preventDefault()
        const input = document.querySelector<HTMLInputElement>(
          'input[aria-label="Import thread file"]'
        )
        if (input && !input.disabled) input.click()
        return
      }
      // Ctrl+, open settings
      if (e.ctrlKey && e.key === ',') {
        e.preventDefault()
        useSettings.getState().setSettingsOpen(true)
        return
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [streamingActive, stop, settings, currentId, send])

  return (
    <main
      className="flex-1 flex flex-col bg-slate-50/85 dark:bg-[rgba(10,14,26,0.3)]"
      aria-busy={streamingActive}
    >
      <div className="flex items-center gap-2.5 px-5 py-4 border-b border-border bg-white/90 text-slate-900 shadow-[0_20px_40px_rgba(15,23,42,0.12)] dark:bg-[rgba(17,24,39,0.9)] dark:text-white dark:shadow-[0_4px_16px_rgba(0,0,0,0.5)] backdrop-blur-3xl justify-between">
        <div className="flex gap-2 items-center flex-wrap">
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
          {currentId && typeof currentId === 'number' && <SummaryIndicator threadId={currentId} />}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => useHelp.getState().openHelp()}
            aria-label="Open keyboard shortcuts"
          >
            Help
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              if (!currentId) return
              const t =
                useThreads.getState().threads.find((x) => x.id === currentId)?.title ||
                `Thread #${currentId}`
              usePrompt.getState().openPrompt({
                title: 'Rename thread',
                defaultValue: t,
                confirmText: 'Rename',
                onSubmit: async (name) => {
                  if (!name.trim() || typeof currentId !== 'number') return
                  await useThreads.getState().renameThread(currentId, name)
                  useToasts.getState().push({ type: 'success', text: 'Thread renamed' })
                },
              })
            }}
            disabled={!currentId || streamingActive}
            aria-label="Rename thread"
          >
            Rename
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              if (!currentId) return
              const t =
                useThreads.getState().threads.find((x) => x.id === currentId)?.title ||
                `Thread #${currentId}`
              useConfirm.getState().openConfirm({
                title: 'Delete thread?',
                description: `"${t}" will be permanently removed.`,
                confirmText: 'Delete',
                onConfirm: async () => {
                  if (typeof currentId !== 'number') return
                  await useThreads.getState().deleteThread(currentId)
                  useToasts.getState().push({ type: 'success', text: 'Thread deleted' })
                },
              })
            }}
            disabled={!currentId || streamingActive}
            aria-label="Delete thread"
          >
            Delete
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              useSettings.setState((s) => ({ theme: s.theme === 'dark' ? 'light' : 'dark' }))
            }
            aria-label="Toggle theme"
          >
            Theme
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={async () => {
              if (!currentId) return
              const { ok, data } = await api(`/api/threads/${currentId}/export`)
              if (ok && data) {
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
                const a = document.createElement('a')
                a.href = URL.createObjectURL(blob)
                a.download = `thread-${currentId}.json`
                a.click()
                useToasts.getState().push({ type: 'success', text: 'Exported thread JSON' })
              } else {
                useToasts.getState().push({ type: 'error', text: 'Export failed' })
              }
            }}
            disabled={!currentId || streamingActive}
            aria-label="Export thread"
          >
            Export
          </Button>
          <label style={{ display: 'inline-block' }} aria-label="Import thread from JSON">
            <input
              type="file"
              style={{ display: 'none' }}
              aria-label="Import thread file"
              onChange={async (e) => {
                const f = e.currentTarget.files?.[0]
                if (!f) return
                const text = await f.text()
                try {
                  const obj = JSON.parse(text)
                  const res = await api('/api/threads/import', { method: 'POST', json: obj })
                  if (res.ok && res.data?.id) {
                    await useThreads.getState().refresh()
                    useThreads.getState().setCurrent(res.data.id)
                    useToasts
                      .getState()
                      .push({ type: 'success', text: `Imported to thread #${res.data.id}` })
                  } else {
                    useToasts.getState().push({ type: 'error', text: 'Import failed' })
                  }
                } catch {
                  useToasts.getState().push({ type: 'error', text: 'Invalid JSON file' })
                }
                e.currentTarget.value = ''
              }}
              disabled={streamingActive as any}
            />
            <span
              style={{
                border: '1px solid var(--border)',
                padding: '6px 10px',
                borderRadius: 8,
                cursor: 'pointer',
                opacity: streamingActive ? 0.6 : 1,
              }}
            >
              Import
            </span>
          </label>
          {streamingActive ? (
            <Button variant="ghost" size="sm" onClick={stop} aria-label="Stop streaming">
              Stop
            </Button>
          ) : null}
          <AuthControls />
          <SettingsButton />
        </div>
      </div>
      <div
        className="flex-1 overflow-auto p-6 flex flex-col gap-4 scroll-smooth"
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
                showModel={settings.showModel}
                showTimestamps={settings.showTimestamps}
                showMeta={settings.showMeta}
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
      <div className="flex gap-3 px-5 py-4 border-t border-border bg-white/95 text-slate-900 shadow-[0_-18px_40px_rgba(15,23,42,0.12)] dark:bg-[rgba(17,24,39,0.9)] dark:text-white dark:shadow-[0_-4px_16px_rgba(0,0,0,0.5)] backdrop-blur-3xl">
        <textarea
          rows={2}
          style={{ flex: 1 }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={streamingActive}
          onKeyDown={(e) => {
            if (!streamingActive && e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              if (currentId && input.trim()) {
                send(currentId, input.trim(), 'user', settings.streaming === 'sse')
                setInput('')
              }
            } else if (!streamingActive && e.key === 'ArrowUp' && !input.trim()) {
              // Edit last user message when input empty
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
                send(currentId, input.trim(), 'user', settings.streaming === 'sse')
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
    </main>
  )
}

function SettingsButton() {
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
        const key = map[k]
        if (key) serverSettings[key] = v
      })
      if (Object.keys(serverSettings).length) {
        await api('/api/settings', { method: 'PUT', json: { token, settings: serverSettings } })
      }
    }
  }
  return (
    <>
      <Button variant="ghost" size="sm" onClick={() => setOpen(true)} aria-label="Open settings">
        Settings
      </Button>
      <Suspense fallback={null}>
        <SettingsModal
          open={open}
          onOpenChange={setOpen}
          settings={s}
          onSettingsChange={(newSettings) => update(newSettings)}
        />
      </Suspense>
    </>
  )
}

export default function App() {
  const { theme, settingsOpen, setSettingsOpen, ...settings } = useSettings()
  useEffect(() => {
    document.documentElement.classList.toggle('light', theme === 'light')
    localStorage.setItem('theme', theme)
  }, [theme])
  return (
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
      <Toasts />
    </div>
  )
}
