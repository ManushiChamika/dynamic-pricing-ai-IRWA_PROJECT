import React from 'react'

interface EmptyStateProps {
  message: string
}

function EmptyStateComponent({ message }: EmptyStateProps) {
  return <div className="text-center py-12 px-6 text-muted text-base">{message}</div>
}

export const EmptyState = React.memo(EmptyStateComponent)
