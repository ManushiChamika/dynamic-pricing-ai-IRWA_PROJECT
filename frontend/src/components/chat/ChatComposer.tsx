import { useState } from 'react'
import { Button } from '../ui/button'
import { useMessagesActions, useStreamingState, useMessages } from '../../stores/messageStore'
import { usePrompt } from '../../stores/promptStore'
import { useThreads } from '../../stores/threadStore'
import { api } from '../../lib/apiClient'
import { useToasts } from '../../stores/toastStore'

interface ChatComposerProps {
  currentId: number | string | null
  streaming: string | undefined
}

export function ChatComposer({ currentId, streaming }: ChatComposerProps) {
  const [input, setInput] = useState('')
  const { send, stop, refresh } = useMessagesActions()
  const { streamingActive } = useStreamingState()
  const messages = useMessages((state) => state.messages)

  const handleSend = () => {
    if (!currentId || !input.trim()) return
    send(currentId as any, input.trim(), 'user', streaming === 'sse')
    setInput('')
  }

  return (
    <>
      <div className="flex gap-3 px-6 py-3 border-t">
        <textarea
          className="flex-1 min-h-[80px] rounded-lg border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 resize-none"
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={streamingActive}
          onKeyDown={(e) => {
            if (!streamingActive && e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            } else if (!streamingActive && e.key === 'ArrowUp' && !input.trim()) {
              const lastUser = [...messages].reverse().find((m) => m.role === 'user')
              if (lastUser) {
                e.preventDefault()
                usePrompt.getState().openPrompt({
                  title: 'Edit last message',
                  defaultValue: lastUser.content,
                  textarea: true,
                  confirmText: 'Save',
                  onSubmit: async (content) => {
                    await useMessages.getState().edit(lastUser.id, content)
                    if (currentId) await refresh(currentId)
                  },
                })
              }
            }
          }}
          aria-label="Message input"
          placeholder="Type a message..."
        />
        {!streamingActive ? (
          <Button
            onClick={handleSend}
            disabled={!currentId || !input.trim()}
            aria-label="Send message"
          >
            Send
          </Button>
        ) : (
          <Button variant="destructive" onClick={stop} aria-label="Stop streaming">
            Stop
          </Button>
        )}
      </div>
      <label style={{ display: 'none' }} aria-label="Import thread from JSON">
        <input
          type="file"
          aria-label="Import thread file"
          onChange={async (e) => {
            const f = e.currentTarget.files?.[0]
            if (!f) return
            const text = await f.text()
            try {
              const obj = JSON.parse(text)
              const res = await api('/api/threads/import', { method: 'POST', json: obj })
              if (res.ok && (res.data as any)?.id) {
                await useThreads.getState().refresh()
                useThreads.getState().setCurrent((res.data as any).id)
                useToasts.getState().push({
                  type: 'success',
                  text: `Imported to thread #${(res.data as any).id}`,
                })
              } else {
                useToasts.getState().push({ type: 'error', text: 'Import failed' })
              }
            } catch {
              useToasts.getState().push({ type: 'error', text: 'Invalid JSON file' })
            }
            ;(e.currentTarget as HTMLInputElement).value = ''
          }}
          disabled={streamingActive as any}
        />
      </label>
    </>
  )
}
