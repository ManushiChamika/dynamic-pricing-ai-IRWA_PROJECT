import React, { useEffect, useRef, useState, lazy, Suspense } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useSpring, animated } from '@react-spring/web'
import { Button } from './ui/button'
import { AgentBadgeGroup } from './AgentBadge'
import { BranchNavigator } from './BranchNavigator'
import { MetadataTooltip } from './MetadataTooltip'
import { ThinkingTokens } from './ThinkingTokens'
import {
  useMessages,
  useMessagesActions,
  useStreamingState,
  type Message,
} from '../stores/messageStore'
import { useThreads, useCurrentThread } from '../stores/threadStore'
import { useSettings } from '../stores/settingsStore'
import { usePrompt } from '../stores/promptStore'
import { useConfirm } from '../stores/confirmStore'
import { useToasts } from '../stores/toastStore'

const markdownComponents = {
  li: ({ children, ...props }: React.LiHTMLAttributes<HTMLLIElement>) => (
    <li className="my-0 py-0 leading-normal" {...props}>{children}</li>
  ),
  ul: ({ children, ...props }: React.HTMLAttributes<HTMLUListElement>) => (
    <ul className="list-disc list-inside my-0 py-0 space-y-1" {...props}>{children}</ul>
  ),
  ol: ({ children, ...props }: React.OlHTMLAttributes<HTMLOListElement>) => (
    <ol className="list-decimal list-inside my-0 py-0 space-y-1" {...props}>{children}</ol>
  ),
  p: ({ children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
    <p className="my-0 py-0 leading-normal inline" {...props}>{children}</p>
  ),
}

const PriceChart = lazy(() => import('./PriceChart').then((m) => ({ default: m.PriceChart })))

export function EditButton({ m }: { m: Message }) {
  const { edit, refresh } = useMessagesActions()
  const streamingActive = useMessages((state) => state.streamingActive)
  const currentId = useCurrentThread()
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

export function BranchButtons({ m }: { m: Message }) {
  const { branch, fork, refresh } = useMessagesActions()
  const streamingActive = useMessages((state) => state.streamingActive)
  const currentId = useCurrentThread()
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

export function MessageView({
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
  const { del, refresh } = useMessagesActions()
  const { streamingActive, liveActiveAgent, liveTool } = useStreamingState()
  const currentId = useCurrentThread()
  const showThinking = useSettings((state) => state.showThinking)

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
      if (!(el as any).matches(':hover')) return
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
  const showAgentBadges = m.role === 'assistant' && agentNames.length > 0

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
      {showAgentBadges ? (
        <div className="agent-badges-container">
          <AgentBadgeGroup
            agents={agentNames}
            activeAgent={streamingActive ? liveActiveAgent : null}
            variant="pill"
          />
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
         <div
           className={`${m.role === 'user' ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white border-0 shadow-[0_4px_12px_rgba(99,102,241,0.3),0_2px_4px_rgba(99,102,241,0.2)]' : 'bg-gradient-to-br from-slate-800/70 to-slate-900/80 backdrop-blur-3xl border-indigo-500/20'} border rounded-2xl px-5 py-4 transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] shadow-[0_4px_12px_rgba(0,0,0,0.4),0_2px_4px_rgba(0,0,0,0.3)] leading-normal relative`}
         >
            {m.role === 'assistant' ? (
              <div className="max-w-none leading-normal">
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={markdownComponents}
                >
                  {m.content || ''}
                </ReactMarkdown>
              </div>
            ) : (
              <pre className="whitespace-pre-wrap">{m.content}</pre>
            )}
        </div>
      {showThinking && m.thinking && m.role === 'assistant' ? (
        <ThinkingTokens thinking={m.thinking} />
      ) : null}
      {m.metadata?.priceData && m.role === 'assistant' ? (
        <div style={{ marginTop: 12 }}>
          <Suspense fallback={<div className="chart-loading">Loading chart…</div>}>
            <PriceChart
              data={m.metadata.priceData as any}
              sku={(m.metadata as any).sku || 'Product'}
              theme={useSettings.getState().theme}
            />
          </Suspense>
        </div>
      ) : null}
      {m.id > 0 && allMessages.length > 0 ? (
        <BranchNavigator
          message={m as any}
          allMessages={allMessages as any}
          onNavigate={(targetId: number) => {
            const targetEl = document.querySelector(`[data-message-id="${targetId}"]`)
            if (targetEl) {
              targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
              targetEl.classList.add('highlight-pulse')
              setTimeout(() => targetEl.classList.remove('highlight-pulse'), 2000)
            }
          }}
        />
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
        {showMeta ? <MetadataTooltip message={m as any} /> : null}
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
