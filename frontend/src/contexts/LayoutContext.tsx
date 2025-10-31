import React, { useMemo, useEffect, useState } from 'react'
import { useSidebar } from '../stores/sidebarStore'
import { usePanels } from '../stores/panelsStore'

type Props = { children: React.ReactNode }

export function LayoutProvider({ children }: Props) {
  const leftCollapsed = useSidebar((s) => s.collapsed)
  const rightCollapsed = usePanels((s) => s.pricesCollapsed)

  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    const mq = window.matchMedia('(max-width: 767px)')
    const onChange = (e: MediaQueryListEvent | MediaQueryList) => setIsMobile(!!e.matches)
    setIsMobile(mq.matches)
    if (mq.addEventListener) mq.addEventListener('change', onChange)
    else mq.addListener(onChange)
    return () => {
      if (mq.removeEventListener) mq.removeEventListener('change', onChange)
      else mq.removeListener(onChange)
    }
  }, [])

  const leftPx = isMobile ? (leftCollapsed ? 0 : 256) : leftCollapsed ? 64 : 256
  const rightPx = isMobile ? (rightCollapsed ? 0 : 280) : rightCollapsed ? 48 : 280

  const style = useMemo(
    () =>
      ({
        ['--left-w' as any]: `${leftPx}px`,
        ['--right-w' as any]: `${rightPx}px`,
      }) as React.CSSProperties,
    [leftPx, rightPx]
  )
  return (
    <div style={style} className="h-full">
      {children}
    </div>
  )
}
