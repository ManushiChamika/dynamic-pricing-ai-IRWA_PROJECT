import { useRef } from 'react'
import { useAutoFocusOnOpen } from '@/lib/modal'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog'
import { DIALOG_MAX_W_CLASS } from '@/lib/constants'
import { usePrompt } from '../stores/promptStore'
import { useToasts } from '../stores/toastStore'

export function PromptModal() {
  const { open, title, value, textarea, confirmText, submitting, onSubmit } = usePrompt()
  const setState = usePrompt.setState
  const inputRef = useRef<HTMLTextAreaElement | HTMLInputElement | null>(null)

  // Focus input when dialog opens
  useAutoFocusOnOpen(inputRef, open)

  const handleConfirm = async () => {
    if (!onSubmit) return usePrompt.getState().close()
    setState({ submitting: true })
    try {
      await onSubmit(value)
      usePrompt.getState().close()
    } catch (e: any) {
      useToasts.getState().push({ type: 'error', text: e?.message || 'Action failed' })
      setState({ submitting: false })
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => !isOpen && !submitting && usePrompt.getState().close()}
    >
      <DialogContent className={DIALOG_MAX_W_CLASS}>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          {textarea ? (
            <Textarea
              ref={inputRef as any}
              rows={6}
              value={value}
              onChange={(e) => setState({ value: e.target.value })}
              disabled={submitting}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.ctrlKey && !submitting) {
                  e.preventDefault()
                  handleConfirm()
                }
              }}
            />
          ) : (
            <Input
              ref={inputRef as any}
              value={value}
              onChange={(e) => setState({ value: e.target.value })}
              disabled={submitting}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !submitting) {
                  e.preventDefault()
                  handleConfirm()
                }
              }}
            />
          )}
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => usePrompt.getState().close()}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button onClick={handleConfirm} disabled={submitting || !value.trim()}>
            {confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
