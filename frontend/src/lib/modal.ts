import { useEffect, RefObject } from 'react'

export function useAutoFocusOnOpen<T extends HTMLTextAreaElement | HTMLInputElement>(
  ref: RefObject<T | null>,
  open: boolean
) {
  useEffect(() => {
    if (open && ref.current) {
      setTimeout(() => {
        const input = ref.current
        if (input) {
          input.focus()
          try {
            ;(input as any).select?.()
          } catch {
            // intentionally ignore selection errors to satisfy no-empty
          }
        }
      }, 0)
    }
  }, [open, ref])
}
