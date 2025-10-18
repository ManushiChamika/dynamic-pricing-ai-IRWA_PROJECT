import { api } from './apiClient'
import type { Message } from '../stores/messageStore'

export async function fetchMessages(threadId: number | string): Promise<Message[]> {
  const { ok, data } = await api(`/api/threads/${threadId}/messages`)
  if (ok && Array.isArray(data)) return data
  return []
}

export async function sendMessage(
  threadId: number,
  content: string,
  userName: string
): Promise<void> {
  await api(`/api/threads/${threadId}/messages`, {
    method: 'POST',
    json: { content, user_name: userName },
  })
}

export async function editMessage(id: number, content: string): Promise<boolean> {
  const res = await api(`/api/messages/${id}`, {
    method: 'PATCH',
    json: { content, branch: true },
  })
  return res.ok
}

export async function deleteMessage(id: number): Promise<void> {
  await api(`/api/messages/${id}`, { method: 'DELETE' })
}

export async function branchMessage(
  threadId: number,
  parentId: number,
  content: string,
  userName: string
): Promise<void> {
  await api(`/api/threads/${threadId}/messages`, {
    method: 'POST',
    json: { content, user_name: userName, parent_id: parentId },
  })
}

export async function forkThread(
  threadId: number,
  atMessage: Message,
  title: string
): Promise<number | null> {
  const messages = await fetchMessages(threadId)
  if (messages.length === 0) return null

  const subset = messages.filter((x) => x.id <= atMessage.id)
  const payload = {
    title: title || `Fork of #${threadId}`,
    messages: subset.map((x) => ({
      id: x.id,
      role: x.role,
      content: x.content,
      model: x.model || null,
      token_in: x.token_in ?? null,
      token_out: x.token_out ?? null,
      cost_usd: x.cost_usd ?? null,
      agents: x.agents ?? null,
      tools: x.tools ?? null,
      api_calls: x.api_calls ?? null,
      parent_id: x.parent_id ?? null,
      metadata: x.metadata ?? null,
    })),
  }

  const res = await api('/api/threads/import', { method: 'POST', json: payload })
  if (res.ok && res.data?.id) return res.data.id
  return null
}
