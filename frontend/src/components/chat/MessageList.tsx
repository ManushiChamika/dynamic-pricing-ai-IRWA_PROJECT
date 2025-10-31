import React from 'react'
import { AnimatePresence } from 'framer-motion'
import { MessageView } from './MessageView'
import { type Message } from '../../stores/messageStore'

interface MessageListProps {
  messages: Message[]
  showModel: boolean
  showTimestamps: boolean
  showMeta: boolean
}

function MessageListComponent({ messages, showModel, showTimestamps, showMeta }: MessageListProps) {
  return (
    <AnimatePresence mode="popLayout">
      {messages.map((m) => (
        <MessageView
          key={m.id}
          m={m}
          showModel={showModel}
          showTimestamps={showTimestamps}
          showMeta={showMeta}
          allMessages={messages}
        />
      ))}
    </AnimatePresence>
  )
}

export const MessageList = React.memo(MessageListComponent)
