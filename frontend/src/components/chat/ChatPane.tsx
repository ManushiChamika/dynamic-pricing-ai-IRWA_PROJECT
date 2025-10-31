import React, { useEffect, useRef } from 'react'
import { useMessages, useMessagesActions } from '../../stores/messageStore'
import { useCurrentThread, useThreads } from '../../stores/threadStore'
import { useSettings, useDisplaySettings, useAppMode } from '../../stores/settingsStore'
import { useAuthToken } from '../../stores/authStore'
import { ChatHeader } from './ChatHeader'
import { ChatComposer } from './ChatComposer'
import { DraftMessageView } from './DraftMessageView'
import { EmptyState } from './EmptyState'
import { VirtualizedMessageList } from './VirtualizedMessageList'
import { useChatSettings } from '../../hooks/useChatSettings'
import { useChatKeyboardShortcuts } from '../../hooks/useChatKeyboardShortcuts'

export function ChatPane() {
  const messages = useMessages((state) => state.messages)
  const { refresh } = useMessagesActions()
  const streamingActive = useMessages((state) => state.streamingActive)
  const currentId = useCurrentThread()
  const displaySettings = useDisplaySettings()
  const { mode, streaming } = useAppMode()
  const token = useAuthToken()
  const msgsRef = useRef<HTMLDivElement | null>(null)

  useChatSettings(token)
  useChatKeyboardShortcuts(currentId, streamingActive, streaming, () => {})

  useEffect(() => {
    if (currentId) {
      const isDraft = String(currentId).startsWith('draft_')
      const shouldSkip = useThreads.getState().skipNextRefresh
      if (shouldSkip) {
        useThreads.setState({ skipNextRefresh: false })
      } else if (!isDraft) {
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
    if (mode === 'developer') {
      useSettings.setState({ showMeta: true, showTimestamps: true })
    }
  }, [mode])

  return (
    <main className="flex-1 min-w-0 flex flex-col bg-background transition-[padding] duration-300 ease-in-out motion-reduce:transition-none">
      <ChatHeader />
      <div
        className="flex-1 overflow-auto bg-gradient-to-b from-background to-muted/10 scroll-smooth"
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
                {isDraft && <DraftMessageView />}
                <VirtualizedMessageList
                  messages={messages}
                  showModel={displaySettings.showModel}
                  showTimestamps={displaySettings.showTimestamps}
                  showMeta={displaySettings.showMeta}
                />
              </>
            ) : (
              <EmptyState message="No messages yet. Say hello!" />
            )
          })()
        ) : (
          <EmptyState message="Select or create a thread to begin." />
        )}
      </div>
      <ChatComposer currentId={currentId} streaming={streaming} />
    </main>
  )
}
