import React from 'react'

function LiveStatusComponent({
  liveActiveAgent,
  liveTool,
}: {
  liveActiveAgent: string | null
  liveTool: { name: string; status: string } | null
}) {
  return (
    <div
      className="mt-2 opacity-70 text-xs flex gap-2 flex-wrap mb-1"
      style={{ marginBottom: 4 }}
    >
      {liveActiveAgent ? (
        <span className="text-xs opacity-95 border border-accent px-3 py-1 rounded-xl bg-gradient-to-br from-accent-light to-purple-500/15 text-accent font-medium transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] shadow-[0_2px_4px_rgba(99,102,241,0.1)]">
          Agent: {liveActiveAgent}
        </span>
      ) : null}
      {liveTool ? (
        <span
          className={`text-xs opacity-95 border border-accent px-3 py-1 rounded-xl bg-gradient-to-br from-accent-light to-purple-500/15 text-accent font-medium transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] shadow-[0_2px_4px_rgba(99,102,241,0.1)] ${liveTool.status === 'done' ? 'opacity-70' : ''}`}
        >
          {liveTool.status === 'running' ? (
            <span className="inline-block w-3.5 h-3.5 border-2 border-accent-light border-t-accent rounded-full animate-spin mr-1.5" />
          ) : null}
          Tool: {liveTool.name} {liveTool.status === 'running' ? '(running…) ' : '(done)'}
        </span>
      ) : null}
    </div>
  )
}

export const LiveStatus = React.memo(LiveStatusComponent)
