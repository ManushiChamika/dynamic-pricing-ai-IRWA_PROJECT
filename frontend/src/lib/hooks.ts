import { useEffect } from 'react'
import { INPUT_TAGS } from '@/lib/constants'

export type Shortcut = {
  when?: () => boolean
  handler: (e: KeyboardEvent) => void
}

// Register a keydown listener with optional predicate; cleans up automatically
export function useGlobalShortcuts(shortcuts: Shortcut[]) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      for (const sc of shortcuts) {
        if (!sc) continue
        try {
          if (!sc.when || sc.when()) sc.handler(e)
        } catch {
          // no-op
        }
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [shortcuts])
}

// Is the current focus inside an input-like element
export function isInInput(el: Element | null = document.activeElement): boolean {
  const tag = (el as HTMLElement | null)?.tagName || ''
  if (INPUT_TAGS.has(tag)) return true
  return !!(el as HTMLElement | null)?.isContentEditable
}
