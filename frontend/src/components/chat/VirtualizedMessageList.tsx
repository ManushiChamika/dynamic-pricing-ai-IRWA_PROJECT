import React from 'react'
import { Virtuoso } from 'react-virtuoso'
import { AnimatePresence } from 'framer-motion'
import { MessageView } from './MessageView'
import { type Message } from '../../stores/messageStore'

interface VirtualizedMessageListProps {
  messages: Message[]
  showModel: boolean
  showTimestamps: boolean
  showMeta: boolean
  onScroll?: (isNearBottom: boolean) => void
}

export const VirtualizedMessageList: React.FC<VirtualizedMessageListProps> = ({
  messages,
  showModel,
  showTimestamps,
  showMeta,
  onScroll,
}) => {
  return (
    <Virtuoso
      data={messages}
      increaseViewportBy={{ top: 200, bottom: 200 }}
      style={{ height: '100%', width: '100%' }}
      itemContent={(index, message) => (
        <AnimatePresence mode="popLayout" key={message.id}>
          <MessageView
            key={message.id}
            m={message}
            showModel={showModel}
            showTimestamps={showTimestamps}
            showMeta={showMeta}
            allMessages={messages}
          />
        </AnimatePresence>
      )}
      overscan={10}
      isScrolling={(isScrolling) => {
        if (!isScrolling && onScroll) {
          onScroll(true)
        }
      }}
      className="px-3 md:px-6 py-4 flex flex-col items-center gap-4"
    />
  )
}
