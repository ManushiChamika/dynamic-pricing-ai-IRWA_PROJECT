import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog'
import { useConfirm } from '../stores/confirmStore'
import { useToasts } from '../stores/toastStore'

export function ConfirmModal() {
  const { open, title, description, confirmText, cancelText, busy, onConfirm } = useConfirm()
  const setState = useConfirm.setState

  const handleConfirm = async () => {
    if (!onConfirm) return useConfirm.getState().close()
    setState({ busy: true })
    try {
      await onConfirm()
      useConfirm.getState().close()
    } catch (e: any) {
      useToasts.getState().push({ type: 'error', text: e?.message || 'Action failed' })
      setState({ busy: false })
    }
  }

  return (
    <AlertDialog
      open={open}
      onOpenChange={(isOpen) => !isOpen && !busy && useConfirm.getState().close()}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={busy}>{cancelText}</AlertDialogCancel>
          <AlertDialogAction onClick={handleConfirm} disabled={busy}>
            {confirmText}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
