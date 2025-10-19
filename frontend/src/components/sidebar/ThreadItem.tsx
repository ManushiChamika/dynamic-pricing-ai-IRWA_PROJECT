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
}

export const ThreadItem = React.memo(
  ({ id, title, isActive, isDraft = false, updatedAt, onSelect }: ThreadItemProps) => {
    const [isHovered, setIsHovered] = useState(false)

    return (
      <li
        className="thread-item group relative cursor-pointer mb-2 transition-all duration-150 ease-out list-none"
        style={{
          background: isActive
            ? 'var(--accent-color)'
            : isHovered
              ? 'var(--thread-item-bg-hover)'
              : 'var(--thread-item-bg-rest)',
          borderRadius: '8px',
          padding: '10px 12px',
          border: isActive
            ? '1px solid var(--accent-color)'
            : isHovered
              ? '1px solid var(--thread-item-border-hover)'
              : '1px solid var(--thread-item-border-rest)',
          boxShadow: isActive
            ? 'var(--thread-item-shadow-active)'
            : isHovered
              ? 'var(--thread-item-shadow-hover)'
              : 'none',
          minHeight: '44px',
          display: 'flex',
          alignItems: 'center',
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={onSelect}
        aria-current={isActive ? 'true' : undefined}
      >
        <div className="flex items-center gap-3 w-full">
          <div
            className="flex-shrink-0 transition-all duration-150"
            style={{
              opacity: isActive ? 1 : isHovered ? 0.9 : 0.6,
              color: isActive ? 'rgba(255, 255, 255, 0.95)' : isHovered ? 'var(--accent-color)' : 'var(--muted)',
              transform: isHovered ? 'scale(1.08)' : 'scale(1)',
            }}
          >
            <MessageSquare size={17} strokeWidth={isActive ? 2.5 : 2} />
          </div>

          <div className="flex-1 min-w-0 flex flex-col gap-1.5">
            <div
              className="text-sm leading-tight overflow-hidden text-ellipsis whitespace-nowrap"
              style={{
                fontWeight: isActive ? 600 : isHovered ? 500 : 450,
                color: isActive ? 'rgba(255, 255, 255, 0.98)' : isHovered ? 'var(--fg)' : 'var(--fg)',
                letterSpacing: '-0.01em',
                opacity: isActive ? 1 : isHovered ? 1 : 0.85,
              }}
            >
              {title}
            </div>

            {updatedAt && !isDraft && (
              <div
                className="text-xs leading-none"
                style={{
                  color: isActive ? 'rgba(255, 255, 255, 0.7)' : 'var(--app-text-muted)',
                  opacity: isActive ? 1 : isHovered ? 0.85 : 0.7,
                  fontWeight: 400,
                }}
              >
                {formatRelativeTime(updatedAt)}
              </div>
            )}
          </div>

          {!isDraft && (
            <div
              className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150"
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
