import { api } from './apiClient'
import type { Thread } from '../stores/threadStore'

export async function loadThreads(): Promise<Thread[]> {
  const { ok, data } = await api('/api/threads')
  if (ok && Array.isArray(data)) return data
  return []
}

export async function createThread(title?: string): Promise<number | null> {
  const { ok, data } = await api('/api/threads', {
    method: 'POST',
    json: { title: title || 'New Thread' },
  })
  if (ok && data?.id) return data.id
  return null
}

export async function deleteThread(id: number): Promise<void> {
  await api(`/api/threads/${id}`, { method: 'DELETE' })
}

export async function renameThread(id: number, title: string): Promise<void> {
  await api(`/api/threads/${id}`, { method: 'PATCH', json: { title } })
}
