import React, { useMemo } from 'react'
import { useSidebar } from '../stores/sidebarStore'
import { usePanels } from '../stores/panelsStore'

type Props = { children: React.ReactNode }

export function LayoutProvider({ children }: Props) {
  const leftCollapsed = useSidebar((s) => s.collapsed)
  const rightCollapsed = usePanels((s) => s.pricesCollapsed)
  const leftPx = leftCollapsed ? 64 : 256
  const rightPx = rightCollapsed ? 48 : 280
  const style = useMemo(
    () => ({ ['--left-w' as any]: `${leftPx}px`, ['--right-w' as any]: `${rightPx}px` } as React.CSSProperties),
    [leftPx, rightPx]
  )
  return (
    <div style={style} className="min-h-full">
      {children}
    </div>
  )
}
