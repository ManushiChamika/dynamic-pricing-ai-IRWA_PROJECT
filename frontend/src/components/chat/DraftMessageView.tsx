import React from 'react'

function DraftMessageViewComponent() {
  return (
    <div className="text-center py-12 px-6 text-muted text-base">
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-accent/20 text-accent border border-accent/30 mb-4">
        Draft conversation
      </div>
      <p>Start typing to begin a new conversation</p>
    </div>
  )
}

export const DraftMessageView = React.memo(DraftMessageViewComponent)
