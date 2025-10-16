import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from './apiClient'

async function fetcher<T>(url: string, init?: RequestInit & { json?: any }): Promise<T> {
  const res = await api<T>(url, init)
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  return res.data as T
}

export function useThreads() {
  return useQuery({
    queryKey: ['threads'],
    queryFn: () => fetcher<any[]>('/api/threads'),
    staleTime: 10000,
  })
}

export function useThreadMessages(threadId: number | null) {
  return useQuery({
    queryKey: ['messages', threadId],
    queryFn: () => fetcher<any[]>(`/api/threads/${threadId}/messages`),
    enabled: threadId !== null,
    staleTime: 5000,
  })
}

export function useCreateThread() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (title: string) => fetcher('/api/threads', { method: 'POST', json: { title } }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['threads'] }) },
  })
}

export function useDeleteThread() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => fetcher(`/api/threads/${id}`, { method: 'DELETE' }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['threads'] }) },
  })
}

export function useSummaries(threadId: number) {
  return useQuery({
    queryKey: ['summaries', threadId],
    queryFn: () => fetcher<{ summaries: any[] }>(`/api/threads/${threadId}/summaries`),
    select: (data) => data.summaries || [],
    staleTime: 30000,
  })
}
