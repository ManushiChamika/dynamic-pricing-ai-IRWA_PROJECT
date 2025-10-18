import React, { useState, useRef, useEffect } from 'react'
import { Button } from './ui/button'

export type HeaderMenuAction = {
  label: string
  onClick: () => void
  disabled?: boolean
  divider?: boolean
}

interface HeaderOverflowMenuProps {
  actions: HeaderMenuAction[]
}

export function HeaderOverflowMenu({ actions }: HeaderOverflowMenuProps) {
  const [open, setOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }

    if (open) {
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [open])

  return (
    <div ref={menuRef} className="relative inline-block">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setOpen(!open)}
        aria-label="More actions"
        className="px-2"
      >
        ⋮
      </Button>

      {open && (
        <div
          className="absolute right-0 mt-1 min-w-[180px] bg-white/95 dark:bg-slate-900/95 border border-border rounded-lg shadow-lg z-50 backdrop-blur-sm overflow-hidden"
          role="menu"
        >
          {actions.map((action, idx) => (
            <React.Fragment key={idx}>
              {action.divider && (
                <div className="h-px bg-border opacity-50 my-1" role="separator" />
              )}
              <button
                onClick={() => {
                  action.onClick()
                  setOpen(false)
                }}
                disabled={action.disabled}
                role="menuitem"
                className="w-full text-left px-4 py-2 text-sm hover:bg-accent/10 dark:hover:bg-accent/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {action.label}
              </button>
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  )
}
