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
