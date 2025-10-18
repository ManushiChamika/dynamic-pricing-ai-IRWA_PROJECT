import React from 'react'
import { Button } from './ui/button'
import {
  useMessages,
  useMessagesActions,
  type Message,
} from '../stores/messageStore'
import { useCurrentThread } from '../stores/threadStore'
import { usePrompt } from '../stores/promptStore'
import { useConfirm } from '../stores/confirmStore'
import { useToasts } from '../stores/toastStore'
import { useThreads } from '../stores/threadStore'

function MessageActionsComponent({ m }: { m: Message }) {
  const { del, edit, branch, fork, refresh } = useMessagesActions()
  const streamingActive = useMessages((state) => state.streamingActive)
  const currentId = useCurrentThread()

  const handleCopy = () => {
    navigator.clipboard.writeText(m.content || '')
  }

  const handleEdit = async () => {
    usePrompt.getState().openPrompt({
      title: 'Edit message',
      defaultValue: m.content,
      textarea: true,
      confirmText: 'Save',
      onSubmit: async (content) => {
        await edit(m.id, content)
        if (currentId) await refresh(currentId)
      },
    })
  }

  const handleDelete = async () => {
    useConfirm.getState().openConfirm({
      title: 'Delete message?',
      description: 'This message will be permanently removed.',
      confirmText: 'Delete',
      onConfirm: async () => {
        await del(m.id)
        if (currentId) await refresh(currentId)
        useToasts.getState().push({ type: 'success', text: 'Message deleted' })
      },
    })
  }

  const handleBranch = async () => {
    if (!currentId) return
    usePrompt.getState().openPrompt({
      title: 'Branch here. Your message:',
      defaultValue: '',
      textarea: true,
      confirmText: 'Branch',
      onSubmit: async (content) => {
        if (!content.trim()) return
        await branch(currentId, m.id, content, 'user')
        await refresh(currentId)
      },
    })
  }

  const handleFork = async () => {
    if (!currentId) return
    usePrompt.getState().openPrompt({
      title: 'Fork thread title',
      defaultValue: `Fork of #${currentId} at message ${m.id}`,
      textarea: false,
      confirmText: 'Fork',
      onSubmit: async (title) => {
        if (!title.trim()) return
        const newId = await fork(currentId, m, title)
        if (newId) {
          useThreads.getState().setCurrent(newId)
          await useThreads.getState().refresh()
          useToasts.getState().push({ type: 'success', text: `Forked to thread #${newId}` })
        }
      },
    })
  }

  return (
    <div className="flex gap-1.5 mt-2 opacity-0 transition-opacity duration-200 hover:opacity-100">
      <Button
        variant="ghost"
        size="sm"
        onClick={handleCopy}
        disabled={streamingActive}
        aria-label="Copy message"
      >
        Copy
      </Button>
      {m.role === 'user' ? (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleEdit}
          disabled={streamingActive}
          aria-label="Edit message"
        >
          Edit
        </Button>
      ) : null}
      <Button
        variant="ghost"
        size="sm"
        onClick={handleDelete}
        disabled={streamingActive}
        aria-label="Delete message"
      >
        Del
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleBranch}
        disabled={streamingActive}
        aria-label="Branch conversation here"
      >
        Branch
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleFork}
        disabled={streamingActive}
        aria-label="Fork new thread from here"
      >
        Fork
      </Button>
    </div>
  )
}

export const MessageActions = React.memo(MessageActionsComponent)
