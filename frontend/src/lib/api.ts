import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

const API_BASE = 'http://localhost:8000'

export interface ApiResponse<T = unknown> {
  ok: boolean
  status: number
  data: T
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('fp_token') || localStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`)
  }

  return response.json()
}

export function useThreads() {
  return useQuery({
    queryKey: ['threads'],
    queryFn: () => fetchApi<any[]>('/api/threads'),
    staleTime: 10000,
  })
}

export function useThreadMessages(threadId: number | null) {
  return useQuery({
    queryKey: ['messages', threadId],
    queryFn: () => fetchApi<any[]>(`/api/threads/${threadId}/messages`),
    enabled: threadId !== null,
    staleTime: 5000,
  })
}

export function useCreateThread() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (title: string) =>
      fetchApi('/api/threads', {
        method: 'POST',
        body: JSON.stringify({ title }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['threads'] })
    },
  })
}

export function useDeleteThread() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) =>
      fetchApi(`/api/threads/${id}`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['threads'] })
    },
  })
}

export function useSummaries(threadId: number) {
  return useQuery({
    queryKey: ['summaries', threadId],
    queryFn: () => fetchApi<{ summaries: any[] }>(`/api/threads/${threadId}/summaries`),
    select: (data) => data.summaries || [],
    staleTime: 30000,
  })
}
