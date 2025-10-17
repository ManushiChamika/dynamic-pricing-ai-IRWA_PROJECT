interface Thread {
  id: number
  title: string
}

interface Message {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at?: string
  model?: string | null
  token_in?: number | null
  token_out?: number | null
  cost_usd?: string | number | null
  api_calls?: number | null
  agents?: { activated?: string[]; count?: number } | null
  tools?: { used?: string[]; count?: number } | null
  metadata?: Record<string, any> | null
  parent_id?: number | null
}

export function exportConversation(thread: Thread, messages: Message[]) {
  const data = {
    version: '1.0',
    exportedAt: new Date().toISOString(),
    thread,
    messages,
  }

  const json = JSON.stringify(data, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `conversation-${thread.id}-${Date.now()}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function importConversation(
  onImport: (data: { thread: Thread; messages: Message[] }) => void
) {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'application/json'
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return

    try {
      const text = await file.text()
      const data = JSON.parse(text)

      if (!data.thread || !data.messages || !Array.isArray(data.messages)) {
        throw new Error('Invalid conversation format')
      }

      onImport({
        thread: data.thread,
        messages: data.messages,
      })
    } catch (error) {
      console.error('Failed to import conversation:', error)
      alert('Failed to import conversation. Please check the file format.')
    }
  }
  input.click()
}
