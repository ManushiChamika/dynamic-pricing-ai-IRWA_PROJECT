import React from 'react'
import { MetadataTooltip } from './MetadataTooltip'
import { type Message } from '../stores/messageStore'

function MessageMetadataComponent({
  m,
  showTimestamps,
  showMeta,
  showModel,
}: {
  m: Message
  showTimestamps: boolean
  showMeta: boolean
  showModel: boolean
}) {
  const hasModelInfo =
    m.role === 'assistant' &&
    showModel &&
    ((m.model && m.model.length > 0) ||
      (m.metadata?.provider &&
        (m.token_in != null || m.token_out != null || m.cost_usd != null)))

  return (
    <div className="mt-2 opacity-70 text-xs flex gap-2 flex-wrap">
      {showTimestamps && m.created_at ? (
        <span className="time" title={m.created_at}>
          {new Date(m.created_at).toLocaleString()}
        </span>
      ) : null}
      {showMeta ? <MetadataTooltip message={m as any} /> : null}
      {hasModelInfo ? (
        <span className="opacity-60 text-[11px] ml-auto" title={m.model || ''}>
          {m.metadata?.provider
            ? `${m.metadata.provider}${m.model ? ':' + m.model : ''}`
            : m.model}
        </span>
      ) : null}
    </div>
  )
}

export const MessageMetadata = React.memo(MessageMetadataComponent)
