import { create } from 'zustand'

export type PromptOpts = {
  title: string
  defaultValue?: string
  textarea?: boolean
  confirmText?: string
  onSubmit: (value: string) => void | Promise<void>
}

export const usePrompt = create<{
  open: boolean
  title: string
  value: string
  textarea: boolean
  confirmText: string
  submitting: boolean
  onSubmit: ((v: string) => void | Promise<void>) | null
  openPrompt: (opts: PromptOpts) => void
  close: () => void
}>(set => ({
  open: false,
  title: '',
  value: '',
  textarea: false,
  confirmText: 'OK',
  submitting: false,
  onSubmit: null,
  openPrompt: (opts) => set({
    open: true,
    title: opts.title,
    value: opts.defaultValue || '',
    textarea: !!opts.textarea,
    confirmText: opts.confirmText || 'OK',
    onSubmit: opts.onSubmit || null,
    submitting: false
  }),
  close: () => set({ open: false, submitting: false })
}))
