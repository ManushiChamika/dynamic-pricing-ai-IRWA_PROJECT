import React from 'react'

interface Props {
  title?: string
  isActive?: boolean
  onClick?: () => void
  children: React.ReactNode
  className?: string
}

export function CollapsedNavItem({ title, isActive, onClick, children, className = '' }: Props) {
  const base = `group relative cursor-pointer mb-1 transition-colors list-none rounded-lg flex items-center justify-center ${
    isActive ? 'bg-secondary text-secondary-foreground' : 'hover:bg-accent hover:text-accent-foreground'
  }`

  return (
    <li className={`${base} ${className}`} onClick={onClick} title={title} style={{ width: 40, height: 40 }}>
      <div className="flex items-center justify-center h-full w-full">{children}</div>
    </li>
  )
}
