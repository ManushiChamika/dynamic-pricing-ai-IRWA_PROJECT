import { create } from 'zustand'

export type ConfirmOpts = {
  title?: string
  description?: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void | Promise<void>
}

export const useConfirm = create<{
  open: boolean
  title: string
  description: string
  confirmText: string
  cancelText: string
  busy: boolean
  onConfirm: (() => void | Promise<void>) | null
  openConfirm: (opts: ConfirmOpts) => void
  close: () => void
}>(set => ({
  open: false,
  title: 'Are you sure?',
  description: 'This action cannot be undone.',
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  busy: false,
  onConfirm: null,
  openConfirm: (opts) => set({
    open: true,
    title: opts.title || 'Are you sure?',
    description: opts.description || 'This action cannot be undone.',
    confirmText: opts.confirmText || 'Confirm',
    cancelText: opts.cancelText || 'Cancel',
    onConfirm: opts.onConfirm,
    busy: false,
  }),
  close: () => set({ open: false, busy: false })
}))
