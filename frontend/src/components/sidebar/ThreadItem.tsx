import React from 'react'
import { SummaryIndicator } from '../SummaryIndicator'

interface ThreadItemProps {
  id: number | string
  title: string
  isActive: boolean
  isDraft?: boolean
  onSelect: () => void
}

export const ThreadItem = React.memo(
  ({ id, title, isActive, isDraft = false, onSelect }: ThreadItemProps) => {
    const handleMouseEnter = (e: React.MouseEvent<HTMLLIElement>) => {
      if (!isActive) {
        const el = e.currentTarget as HTMLElement
        el.style.background = 'var(--accent-light)'
        el.style.borderColor = 'var(--border-color)'
      }
    }

    const handleMouseLeave = (e: React.MouseEvent<HTMLLIElement>) => {
      if (!isActive) {
        const el = e.currentTarget as HTMLElement
        el.style.background = 'transparent'
        el.style.borderColor = 'transparent'
      }
    }

    return (
      <li
        className="px-3 py-2.5 rounded-lg cursor-pointer mb-1.5 transition-all duration-200 border"
        style={{
          background: isActive ? 'var(--accent-color)' : 'transparent',
          color: isActive ? 'white' : 'var(--fg)',
          fontWeight: isActive ? 500 : 400,
          borderColor: 'transparent',
        }}
        onClick={onSelect}
        aria-current={isActive ? 'true' : undefined}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <div className="flex items-center justify-between gap-2">
          <span className="flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-[var(--font-sm)]">
            {title}
          </span>
          {!isDraft && (
            <span onClick={(e) => e.stopPropagation()}>
              <SummaryIndicator threadId={id as number} />
            </span>
          )}
        </div>
      </li>
    )
  }
)

ThreadItem.displayName = 'ThreadItem'
