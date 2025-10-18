import React from 'react'
import { MessageView } from '../MessageView'
import { type Message } from '../../stores/messageStore'

interface MessageListProps {
  messages: Message[]
  showModel: boolean
  showTimestamps: boolean
  showMeta: boolean
}

function MessageListComponent({
  messages,
  showModel,
  showTimestamps,
  showMeta,
}: MessageListProps) {
  return (
    <>
      {messages.map((m) => (
        <MessageView
          key={m.id + ':' + m.created_at}
          m={m}
          showModel={showModel}
          showTimestamps={showTimestamps}
          showMeta={showMeta}
          allMessages={messages}
        />
      ))}
    </>
  )
}

export const MessageList = React.memo(MessageListComponent)
