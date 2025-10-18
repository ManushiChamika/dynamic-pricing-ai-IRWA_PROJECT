import React, { useEffect, useRef, useState, lazy, Suspense } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useSpring, animated } from '@react-spring/web'
import { AgentBadgeGroup } from './AgentBadge'
import { BranchNavigator } from './BranchNavigator'
import { ThinkingTokens } from './ThinkingTokens'
import { MessageActions } from './MessageActions'
import { MessageMetadata } from './MessageMetadata'
import { LiveStatus } from './LiveStatus'
import {
  useMessages,
  useMessagesActions,
  useStreamingState,
  type Message,
} from '../stores/messageStore'
import { useCurrentThread } from '../stores/threadStore'
import { useSettings } from '../stores/settingsStore'
import { useConfirm } from '../stores/confirmStore'
import { useToasts } from '../stores/toastStore'

const MARKDOWN_COMPONENTS = {
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
        useMessages.getState().edit(m.id, m.content).then(() => {
          if (currentId) refresh(currentId)
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
        <LiveStatus liveActiveAgent={liveActiveAgent} liveTool={liveTool} />
      ) : null}
      <div
        className={`${m.role === 'user' ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white border-0 shadow-[0_4px_12px_rgba(99,102,241,0.3),0_2px_4px_rgba(99,102,241,0.2)]' : 'bg-gradient-to-br from-slate-800/70 to-slate-900/80 backdrop-blur-3xl border-indigo-500/20'} border rounded-2xl px-5 py-4 transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] shadow-[0_4px_12px_rgba(0,0,0,0.4),0_2px_4px_rgba(0,0,0,0.3)] leading-normal relative`}
      >
        {m.role === 'assistant' ? (
          <div className="max-w-none leading-normal">
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={MARKDOWN_COMPONENTS}
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
      <MessageActions m={m} />
      <MessageMetadata
        m={m}
        showTimestamps={showTimestamps}
        showMeta={showMeta}
        showModel={showModel}
      />
    </animated.div>
  )
}
