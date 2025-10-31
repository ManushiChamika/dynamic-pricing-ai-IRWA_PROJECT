import { useEffect } from 'react'
import { TOAST_AUTO_DISMISS_MS } from '@/lib/constants'
import { useToasts } from '../stores/toastStore'

export function Toasts() {
  const { toasts, remove } = useToasts()
  useEffect(() => {
    const timers = toasts.map((t) => setTimeout(() => remove(t.id), TOAST_AUTO_DISMISS_MS))
    return () => {
      timers.forEach(clearTimeout)
    }
  }, [toasts, remove])
  return (
    <div
      className="fixed right-5 bottom-5 flex flex-col gap-3 z-50"
      aria-live="polite"
      role="status"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`border rounded-lg px-4 py-3 max-w-[380px] animate-slideInRight text-sm font-medium cursor-pointer ${t.type === 'info' ? 'border-blue-500/50 bg-blue-500/10' : t.type === 'success' ? 'border-green-500/50 bg-green-500/10' : 'border-destructive/50 bg-destructive/10'}`}
          onClick={() => remove(t.id)}
          title="Click to dismiss"
        >
          {t.text}
        </div>
      ))}
    </div>
  )
}
