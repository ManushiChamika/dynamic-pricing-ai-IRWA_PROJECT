import React, { useState, useEffect, useRef } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { useToasts } from '../../stores/toastStore'
import { api } from '../../lib/apiClient'
import { sanitizeFileName, buildMarkdown } from '../../utils/exportHelpers'

export function ExportThreadModal({
  open,
  onOpenChange,
  threadId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  threadId?: number | null
}) {
  const [format, setFormat] = useState<'md' | 'txt' | 'json'>('md')
  const [includeMeta, setIncludeMeta] = useState(false)
  const [filename, setFilename] = useState('')
  const [working, setWorking] = useState(false)
  const [progress, setProgress] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const toasts = useToasts.getState()

  useEffect(() => {
    if (open) {
      const base = threadId ? `thread-${threadId}` : 'thread'
      setFilename(`${base}.${format}`)
    }
  }, [open, threadId, format])

  const handleClose = () => {
    if (working && abortRef.current) {
      abortRef.current.abort()
    }
    onOpenChange(false)
  }

  const downloadBlob = (blob: Blob, name: string) => {
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = name
    a.click()
    URL.revokeObjectURL(a.href)
  }

  const handleExport = async () => {
    if (!threadId) {
      toasts.getState().push({ type: 'error', text: 'No thread selected' })
      return
    }
    setWorking(true)
    setProgress('Starting...')
    abortRef.current = new AbortController()
    try {
      if (format === 'json') {
        setProgress('Fetching thread data...')
        const { ok, data } = await api(`/api/threads/${threadId}/export`, {
          signal: abortRef.current.signal,
        })
        if (!ok || !data) throw new Error('Export failed: No data received')
        setProgress('Creating file...')
        const blob = new Blob([JSON.stringify(data, null, 2)], {
          type: 'application/json;charset=utf-8',
        })
        downloadBlob(blob, sanitizeFileName(filename))
        toasts.push({ type: 'success', text: 'Exported thread JSON' })
      } else {
        setProgress('Fetching thread data...')
        const { ok, data } = await api(`/api/threads/${threadId}/export`, {
          signal: abortRef.current.signal,
        })
        if (!ok || !data) throw new Error('Export failed: No data received')
        if (!data.messages || data.messages.length === 0) {
          throw new Error('Cannot export empty thread')
        }
        setProgress('Formatting...')
        const md = buildMarkdown(data.thread, data.messages, includeMeta)
        const mime = format === 'md' ? 'text/markdown;charset=utf-8' : 'text/plain;charset=utf-8'
        downloadBlob(new Blob([md], { type: mime }), sanitizeFileName(filename))
        toasts.push({ type: 'success', text: `Exported thread as ${format.toUpperCase()}` })
      }
    } catch (e: any) {
      if (e.name === 'AbortError') {
        toasts.push({ type: 'info', text: 'Export cancelled' })
      } else {
        console.error('Export error:', e)
        toasts.push({ type: 'error', text: e instanceof Error ? e.message : 'Export failed' })
      }
    } finally {
      setWorking(false)
      setProgress(null)
      abortRef.current = null
    }
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !working && onOpenChange(v)}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Export Thread</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          <div className="grid grid-cols-3 gap-3">
            <label className="flex items-center gap-2">
              <input type="radio" checked={format === 'md'} onChange={() => setFormat('md')} />
              <span>Markdown (.md)</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="radio" checked={format === 'txt'} onChange={() => setFormat('txt')} />
              <span>Plain text (.txt)</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="radio" checked={format === 'json'} onChange={() => setFormat('json')} />
              <span>JSON (.json)</span>
            </label>
          </div>
          <div className="mt-3 flex items-center gap-3">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeMeta}
                onChange={(e) => setIncludeMeta(e.target.checked)}
              />
              <span>Include message metadata</span>
            </label>
          </div>
          <div className="mt-3">
            <Input
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              aria-label="Export filename"
            />
          </div>
          {progress ? <div className="mt-3 text-sm text-muted">{progress}</div> : null}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={working}>
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={working || typeof threadId !== 'number'}>
            {working ? 'Exporting…' : 'Export & Save'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
