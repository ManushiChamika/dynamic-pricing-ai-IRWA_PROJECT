import React, { useEffect, useRef, useState } from 'react'
import { SCROLL_STICKY_THRESHOLD_PX } from '@/lib/constants'
import { useMessages, useMessagesActions } from '../stores/messageStore'
import { useCurrentThread } from '../stores/threadStore'
import { useSettings, useDisplaySettings, useAppMode } from '../stores/settingsStore'
import { useAuthToken } from '../stores/authStore'
import { MessageView } from './MessageView'
import { ChatHeader } from './ChatHeader'
import { ChatComposer } from './ChatComposer'
import { useChatSettings } from '../hooks/useChatSettings'
import { useChatKeyboardShortcuts } from '../hooks/useChatKeyboardShortcuts'

export function ChatPane() {
  const messages = useMessages((state) => state.messages)
  const { refresh } = useMessagesActions()
  const streamingActive = useMessages((state) => state.streamingActive)
  const currentId = useCurrentThread()
  const displaySettings = useDisplaySettings()
  const { mode, streaming } = useAppMode()
  const token = useAuthToken()
  const [input, setInput] = useState('')
  const msgsRef = useRef<HTMLDivElement | null>(null)
  const shouldStickRef = useRef(true)

  useChatSettings(token)
  useChatKeyboardShortcuts(currentId, streamingActive, streaming, setInput)
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
    if (currentId) {
      const isDraft = String(currentId).startsWith('draft_')
      if (!isDraft) {
        refresh(currentId)
      } else {
        useMessages.setState({ messages: [] })
      }
    }
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

  return (
    <main className="flex-1 flex flex-col bg-[rgba(10,14,26,0.3)]">
      <ChatHeader />
      <div
        className="flex-1 overflow-auto p-[var(--space-6)] flex flex-col gap-[var(--space-4)] scroll-smooth"
        ref={msgsRef}
        role="log"
        aria-live="polite"
        aria-relevant="additions text"
        aria-label="Chat messages"
      >
        {currentId ? (
          (() => {
            const isDraft = String(currentId).startsWith('draft_')
            return messages.length || isDraft ? (
              <>
                {isDraft && (
                  <div className="text-center py-12 px-6 text-muted text-base">
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-accent/20 text-accent border border-accent/30 mb-4">
                      Draft conversation
                    </div>
                    <p>Start typing to begin a new conversation</p>
                  </div>
                )}
                {messages.map((m) => (
                  <MessageView
                    key={m.id + ':' + m.created_at}
                    m={m}
                    showModel={displaySettings.showModel}
                    showTimestamps={displaySettings.showTimestamps}
                    showMeta={displaySettings.showMeta}
                    allMessages={messages}
                  />
                ))}
              </>
            ) : (
              <div className="text-center py-12 px-6 text-muted text-base">
                No messages yet. Say hello!
              </div>
            )
          })()
        ) : (
          <div className="text-center py-12 px-6 text-muted text-base">
            Select or create a thread to begin.
          </div>
        )}
      </div>
      <ChatComposer currentId={currentId} streaming={streaming} />
    </main>
  )
}
