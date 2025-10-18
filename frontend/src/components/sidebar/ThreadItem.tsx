import React from 'react'
import { SummaryIndicator } from '../SummaryIndicator'
import { formatRelativeTime } from '../../lib/timeUtils'

interface ThreadItemProps {
  id: number | string
  title: string
  isActive: boolean
  isDraft?: boolean
  updatedAt?: string
  onSelect: () => void
}

export const ThreadItem = React.memo(
  ({ id, title, isActive, isDraft = false, updatedAt, onSelect }: ThreadItemProps) => {
    return (
      <li
        className="group relative px-3 py-2 rounded-lg cursor-pointer mb-2 transition-all duration-200"
        style={{
          background: isActive ? 'var(--accent-color)' : 'transparent',
          color: isActive ? 'white' : 'var(--fg)',
        }}
        onMouseEnter={(e) => {
          if (!isActive) {
            e.currentTarget.style.background = 'var(--accent-light)'
          }
        }}
        onMouseLeave={(e) => {
          if (!isActive) {
            e.currentTarget.style.background = 'transparent'
          }
        }}
        onClick={onSelect}
        aria-current={isActive ? 'true' : undefined}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div
              className="text-sm leading-snug mb-0.5 overflow-hidden text-ellipsis whitespace-nowrap"
              style={{ fontWeight: isActive ? 500 : 400 }}
            >
              {title}
            </div>
            {updatedAt && !isDraft && (
              <div
                className="text-xs"
                style={{
                  color: isActive ? 'rgba(255, 255, 255, 0.7)' : 'var(--fg)',
                  opacity: isActive ? 1 : 0.6,
                }}
              >
                {formatRelativeTime(updatedAt)}
              </div>
            )}
          </div>
          {!isDraft && (
            <span className="flex-shrink-0 mt-0.5" onClick={(e) => e.stopPropagation()}>
              <SummaryIndicator threadId={id as number} />
            </span>
          )}
        </div>
      </li>
    )
  }
)

ThreadItem.displayName = 'ThreadItem'
