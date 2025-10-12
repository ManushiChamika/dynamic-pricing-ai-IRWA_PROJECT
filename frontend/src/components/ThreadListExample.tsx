import { useThreads, useCreateThread, useDeleteThread } from '../lib/api'
import { Button } from './ui/button'

export function ThreadListExample() {
  const { data: threads = [], isLoading, error } = useThreads()
  const createThread = useCreateThread()
  const deleteThread = useDeleteThread()

  if (isLoading) return <div>Loading threads...</div>
  if (error) return <div>Error loading threads</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold">Threads (TanStack Query)</h2>
        <Button
          onClick={() => createThread.mutate('New Thread')}
          disabled={createThread.isPending}
        >
          {createThread.isPending ? 'Creating...' : 'New Thread'}
        </Button>
      </div>

      <div className="space-y-2">
        {threads.map((thread: any) => (
          <div key={thread.id} className="flex justify-between items-center p-2 border rounded">
            <span>{thread.title || `Thread ${thread.id}`}</span>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => deleteThread.mutate(thread.id)}
              disabled={deleteThread.isPending}
            >
              Delete
            </Button>
          </div>
        ))}
      </div>
    </div>
  )
}
