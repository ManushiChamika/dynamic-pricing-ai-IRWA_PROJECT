import React, { useState } from 'react'
import { MessageSquare } from 'lucide-react'
import { SummaryIndicator } from '../SummaryIndicator'
import { formatRelativeTime } from '../../lib/timeUtils'

interface ThreadItemProps {
  id: number | string
  title: string
  isActive: boolean
  isDraft?: boolean
  updatedAt?: string
  onSelect: () => void
  collapsed?: boolean
}

export const ThreadItem = React.memo(
  ({ id, title, isActive, isDraft = false, updatedAt, onSelect, collapsed = false }: ThreadItemProps) => {
    if (collapsed) {
      return (
        <li
          className={`group relative cursor-pointer mb-1 transition-colors list-none rounded-lg flex items-center justify-center ${
            isActive
              ? 'bg-secondary text-secondary-foreground'
              : 'hover:bg-accent hover:text-accent-foreground'
          }`}
          onClick={onSelect}
          aria-current={isActive ? 'true' : undefined}
          title={title}
          style={{ width: '40px', height: '40px' }}
        >
          <div className="flex items-center justify-center h-full w-full">
            <MessageSquare className="h-4 w-4 shrink-0" />
          </div>
        </li>
      )
    }

    return (
      <li
        className={`group relative cursor-pointer mb-1 transition-colors list-none rounded-lg px-3 py-2.5 ${
          isActive
            ? 'bg-secondary text-secondary-foreground'
            : 'hover:bg-accent hover:text-accent-foreground'
        }`}
        onClick={onSelect}
        aria-current={isActive ? 'true' : undefined}
      >
        <div className="flex items-center gap-3 w-full">
          <MessageSquare className="h-4 w-4 shrink-0" />

          <div className="flex-1 min-w-0 flex flex-col gap-0.5">
            <div className="overflow-hidden text-ellipsis whitespace-nowrap text-sm font-medium leading-none">
              {title}
            </div>

            {updatedAt && !isDraft && (
              <div className="text-xs text-muted-foreground leading-none">
                {formatRelativeTime(updatedAt)}
              </div>
            )}
          </div>

          {!isDraft && (
            <div
              className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => e.stopPropagation()}
            >
              <SummaryIndicator threadId={id as number} />
            </div>
          )}
        </div>
      </li>
    )
  }
)

ThreadItem.displayName = 'ThreadItem'
