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
          className={`backdrop-blur-2xl bg-panel-solid border rounded-xl px-4 py-3 shadow-lg max-w-[380px] animate-slideInRight text-sm font-medium ${t.type === 'info' ? 'border-blue-500 bg-gradient-to-br from-blue-500/15 to-panel-solid' : t.type === 'success' ? 'border-green-500 bg-gradient-to-br from-green-500/15 to-panel-solid' : 'border-red-500 bg-gradient-to-br from-red-500/15 to-panel-solid'}`}
          onClick={() => remove(t.id)}
          title="Click to dismiss"
        >
          {t.text}
        </div>
      ))}
    </div>
  )
}
