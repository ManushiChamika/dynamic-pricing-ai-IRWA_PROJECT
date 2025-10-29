import React, { useEffect, useRef, useState, lazy, Suspense } from 'react'
import { MarkdownRenderer } from './MarkdownRenderer'
import { AgentBadgeGroup } from '../AgentBadge'
import { BranchNavigator } from '../BranchNavigator'
import { ThinkingTokens } from '../ThinkingTokens'
import { MessageActions } from './MessageActions'
import { MessageMetadata } from './MessageMetadata'
import { LiveStatus } from '../LiveStatus'
import {
  useMessages,
  useMessagesActions,
  useStreamingState,
  type Message,
} from '../../stores/messageStore'
import { useCurrentThread } from '../../stores/threadStore'
import { useSettings } from '../../stores/settingsStore'
import { useConfirm } from '../../stores/confirmStore'
import { useToasts } from '../../stores/toastStore'
import { User, Sparkles } from 'lucide-react'

const PriceChart = lazy(() => import('../PriceChart').then((m) => ({ default: m.PriceChart })))

function MessageViewComponent({
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
        useMessages
          .getState()
          .edit(m.id, m.content)
          .then(() => {
            if (currentId) refresh(currentId)
          })
      } else if (e.key === 'Delete' && m.role === 'user') {
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
    <div
      ref={rowRef}
      className={`group/message w-full max-w-3xl mx-auto animate-slideIn origin-left transition-colors duration-200 rounded-lg ${m.role === 'user' ? 'pl-8 md:pl-16' : 'pr-8 md:pr-16'}`}
      role="article"
      aria-label={`${m.role} message`}
      style={{ backgroundColor: hovered ? 'hsl(var(--accent) / 0.05)' : 'transparent' }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      data-message-id={m.id}
    >
      {showAgentBadges ? (
        <div className="mb-2">
          <AgentBadgeGroup
            agents={agentNames}
            activeAgent={streamingActive ? liveActiveAgent : null}
            variant="pill"
          />
        </div>
      ) : null}
      {m.id === -1 ? <LiveStatus liveActiveAgent={liveActiveAgent} liveTool={liveTool} /> : null}
      <div className={`flex gap-3 items-start ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
        <div
          className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ${m.role === 'user' ? 'bg-muted border-2 border-foreground/40' : 'bg-gradient-to-br from-purple-500 via-violet-500 to-indigo-500 shadow-sm'}`}
        >
          {m.role === 'user' ? (
            <User className="w-5 h-5 text-foreground" strokeWidth={2} />
          ) : (
            <Sparkles className="w-5 h-5 text-white" strokeWidth={1.5} />
          )}
        </div>
        <div className={`${m.role === 'user' ? 'flex-1 flex flex-col items-end' : 'flex-1'}`}>
          <div
            className={`${m.role === 'user' ? 'bg-primary/10 border border-primary/20 text-right inline-block max-w-fit' : 'border border-primary/20 w-full'} rounded-lg px-4 py-3 transition-colors leading-normal`}
            style={
              m.role === 'assistant' ? { background: 'var(--message-assistant-bg)' } : undefined
            }
          >
            {m.role === 'assistant' ? (
              <MarkdownRenderer content={m.content || ''} />
            ) : (
              <pre className="whitespace-pre-wrap text-right">{m.content}</pre>
            )}
          </div>
          {showThinking && m.thinking && m.role === 'assistant' ? (
            <ThinkingTokens thinking={m.thinking} />
          ) : null}
          {m.metadata?.priceData && m.role === 'assistant' ? (
            <div className="mt-3">
              <Suspense
                fallback={
                  <div className="text-center py-4 text-muted-foreground text-sm">
                    Loading chart…
                  </div>
                }
              >
                <PriceChart
                  data={m.metadata.priceData}
                  sku={m.metadata.sku || 'Product'}
                  theme={useSettings.getState().theme}
                />
              </Suspense>
            </div>
          ) : null}
          {m.id > 0 && allMessages.length > 0 ? (
            <BranchNavigator
              message={m}
              allMessages={allMessages}
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
        </div>
      </div>
    </div>
  )
}

export const MessageView = React.memo(MessageViewComponent)
