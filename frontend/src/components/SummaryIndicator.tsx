import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/apiClient'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip'

export interface Summary {
  id: number
  upto_message_id: number
  content: string
  created_at: string | null
}

interface SummaryIndicatorProps {
  threadId: number
}

export function SummaryIndicator({ threadId }: SummaryIndicatorProps) {
  const [open, setOpen] = useState(false)
  const [hasHovered, setHasHovered] = useState(false)
  const { data: summaries = [] } = useQuery({
    queryKey: ['summaries', threadId],
    queryFn: async () => {
      const res = await api<{ summaries: Summary[] }>(`/api/threads/${threadId}/summaries`)
      if (!res.ok) throw new Error(`API Error: ${res.status}`)
      return (res.data?.summaries || []) as Summary[]
    },
    staleTime: 30000,
    enabled: hasHovered,
  })

  if (!hasHovered) {
    return (
      <button
        onMouseEnter={() => setHasHovered(true)}
        onClick={() => {
          setHasHovered(true)
          setOpen(true)
        }}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full
                 bg-indigo-500/20 text-indigo-400 border border-indigo-500/30
                 hover:bg-indigo-500/30 hover:border-indigo-500/50 transition-all duration-200"
        aria-label="View summaries"
      >
        <span>📝</span>
      </button>
    )
  }

  if (summaries.length === 0) return null

  return (
    <>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={() => setOpen(true)}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full
                       bg-indigo-500/20 text-indigo-400 border border-indigo-500/30
                       hover:bg-indigo-500/30 hover:border-indigo-500/50 transition-all duration-200"
              aria-label={`View ${summaries.length} summary${summaries.length > 1 ? 'ies' : ''}`}
            >
              <span>📝</span>
              <span>{summaries.length}</span>
            </button>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs">
            <div className="text-xs">
              <div className="font-semibold">Conversation Summaries</div>
              <div className="text-muted-foreground">
                {summaries.length} summary checkpoint{summaries.length > 1 ? 's' : ''} available.
                Click to view.
              </div>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <span>📝</span>
              <span>Conversation Summaries</span>
              <span className="text-sm font-normal text-muted-foreground">
                ({summaries.length} checkpoint{summaries.length > 1 ? 's' : ''})
              </span>
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            {summaries.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                No summaries available for this thread.
              </div>
            ) : (
              summaries.map((summary, idx) => (
                <div
                  key={summary.id}
                  className="p-4 rounded-lg bg-gray-500/10 border border-gray-500/20 space-y-2"
                >
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="font-medium">
                      Checkpoint #{idx + 1} · Up to message #{summary.upto_message_id}
                    </span>
                    {summary.created_at && (
                      <span>{new Date(summary.created_at).toLocaleString()}</span>
                    )}
                  </div>
                  <div className="text-sm leading-relaxed whitespace-pre-wrap">
                    {summary.content}
                  </div>
                </div>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
