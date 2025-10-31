import React, { useEffect, useRef, useState, lazy, Suspense } from 'react'
import { motion } from 'framer-motion'
import { MarkdownRenderer } from './MarkdownRenderer'
import { BranchNavigator } from '../BranchNavigator'
import { ThinkingTokens } from '../ThinkingTokens'
import { MessageActions } from './MessageActions'
import { MessageMetadata } from './MessageMetadata'
import { AgentActivity } from './AgentActivity'
import { TypingIndicator } from './TypingIndicator'
import { messageVariants } from './animations'
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
  const { streamingActive } = useStreamingState()
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
          .then(async () => {
            if (currentId) {
              await useMessages.getState().branch(currentId as number, m.id, m.content, 'user')
              await refresh(currentId)
            }
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


  return (
    <motion.div
      ref={rowRef}
      className={`group/message w-full max-w-3xl mx-auto origin-left transition-colors duration-200 rounded-lg mb-4 md:mb-6 py-2 md:py-3 ${m.role === 'user' ? 'pl-8 md:pl-16' : 'pr-8 md:pr-16'}`}
      role="article"
      aria-label={`${m.role} message`}
      style={{ backgroundColor: hovered ? 'hsl(var(--accent) / 0.05)' : 'transparent' }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      data-message-id={m.id}
      variants={messageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <div className={`flex gap-3 items-start ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
        <div
          className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ring-1 ring-white/10 ${m.role === 'user' ? 'bg-muted border-2 border-foreground/40' : 'bg-gradient-to-br from-purple-500 via-violet-500 to-indigo-500 shadow-sm'}`}
        >
          {m.role === 'user' ? (
            <User className="w-5 h-5 text-foreground" strokeWidth={2} />
          ) : (
            <Sparkles className="w-5 h-5 text-white" strokeWidth={1.5} />
          )}
        </div>
        <div className={`${m.role === 'user' ? 'flex-1 flex flex-col items-end' : 'flex-1'} space-y-2`}>
          <div
            className={`${m.role === 'user' ? 'bg-primary/10 border border-primary/20 text-right inline-block max-w-[85%] md:max-w-[70%] shadow-sm rounded-2xl px-4 py-3' : 'w-full md:max-w-[85%] px-0 py-0'} transition-colors leading-relaxed`}
            style={undefined}
          >
            {m.role === 'assistant' ? (
              <MarkdownRenderer content={m.content || ''} />
            ) : (
               <pre className="whitespace-pre-wrap text-right leading-relaxed">{m.content}</pre>

            )}
          </div>
          {showThinking && m.thinking && m.role === 'assistant' ? (
            <ThinkingTokens thinking={m.thinking} />
          ) : null}
          {m.role === 'assistant' && (m.agents?.count || 0) > 0 ? (
            <AgentActivity agents={m.agents} tools={m.tools} />
          ) : null}
          {m.metadata?.priceData && m.role === 'assistant' ? (
            <div className="mt-3">
              <Suspense
                fallback={
                  <div className="text-center py-4 text-muted-foreground text-sm">
                    <TypingIndicator />
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
    </motion.div>
  )
}

export const MessageView = React.memo(MessageViewComponent)
