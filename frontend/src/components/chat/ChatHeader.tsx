import { useMemo, useState } from 'react'
import { Button } from '../ui/button'
import { useMessagesActions, useStreamingState } from '../../stores/messageStore'
import { useThreads, useCurrentThread } from '../../stores/threadStore'
import { useHelp } from '../../stores/helpStore'
import { usePrompt } from '../../stores/promptStore'
import { useConfirm } from '../../stores/confirmStore'
import { useToasts } from '../../stores/toastStore'
import { SummaryIndicator } from '../SummaryIndicator'
import { AuthControls } from '../AuthControls'
import { SettingsButton } from '../SettingsButton'
import { HeaderOverflowMenu, type HeaderMenuAction } from '../HeaderOverflowMenu'
import { useSettings } from '../../stores/settingsStore'
import { api } from '../../lib/apiClient'
import { ExportThreadModal } from './ExportThreadModal'

export function ChatHeader() {
  const { stop } = useMessagesActions()
  const { streamingActive, liveActiveAgent, liveTool, liveAgents, turnStats } = useStreamingState()
  const currentId = useCurrentThread()
  const [exportOpen, setExportOpen] = useState(false)

  const headerActions = useMemo<HeaderMenuAction[]>(() => [
      {
        label: 'Rename',
        onClick: () => {
          if (!currentId) return
          const isDraft = String(currentId).startsWith('draft_')
          if (isDraft) {
            useToasts.getState().push({ type: 'error', text: 'Cannot rename draft threads' })
            return
          }
          const t =
            useThreads.getState().threads.find((x) => x.id === currentId)?.title ||
            `Thread #${currentId}`
          usePrompt.getState().openPrompt({
            title: 'Rename thread',
            defaultValue: t,
            confirmText: 'Rename',
            onSubmit: async (name) => {
              if (!name.trim() || typeof currentId !== 'number') return
              await useThreads.getState().renameThread(currentId, name)
              useToasts.getState().push({ type: 'success', text: 'Thread renamed' })
            },
          })
        },
        disabled: !currentId || streamingActive || String(currentId).startsWith('draft_'),
      },
      {
        label: 'Delete',
        onClick: () => {
          if (!currentId) return
          const isDraft = String(currentId).startsWith('draft_')
          if (isDraft) {
            useToasts.getState().push({ type: 'error', text: 'Cannot delete draft threads' })
            return
          }
          const t =
            useThreads.getState().threads.find((x) => x.id === currentId)?.title ||
            `Thread #${currentId}`
          useConfirm.getState().openConfirm({
            title: 'Delete thread?',
            description: `"${t}" will be permanently removed.`,
            confirmText: 'Delete',
            onConfirm: async () => {
              if (typeof currentId !== 'number') return
              await useThreads.getState().deleteThread(currentId)
              useToasts.getState().push({ type: 'success', text: 'Thread deleted' })
            },
          })
        },
        disabled: !currentId || streamingActive || String(currentId).startsWith('draft_'),
      },
      {
        label: 'Open Export...',
        onClick: () => {
          setExportOpen(true)
        },
        disabled: !currentId || streamingActive || String(currentId).startsWith('draft_'),
      },
      {
        label: 'Import',
        onClick: () => {
          const input = document.querySelector<HTMLInputElement>(
            'input[aria-label="Import thread file"]'
          )
          if (input && !input.disabled) input.click()
        },
        disabled: streamingActive,
      },
    ],
    [currentId, streamingActive]
  );

  return (
    <div className="flex items-center gap-3 px-6 py-3 border-b justify-between bg-card/50 transition-[padding] duration-300 ease-in-out">
      <div className="flex gap-2 items-center flex-wrap">
        <strong>Thread</strong>
        <span>#{currentId ?? '-'}</span>
        {streamingActive ? (
          <span
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-accent/20 text-accent border border-accent/30"
            title="Model is streaming a reply"
          >
            <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
            Streaming…
          </span>
        ) : null}
        {streamingActive && liveActiveAgent ? (
          <span
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-purple-500/20 text-purple-400 border border-purple-500/30"
            title="Active agent"
          >
            Agent: {liveActiveAgent}
          </span>
        ) : null}
        {streamingActive && Array.isArray(liveAgents) && liveAgents.length ? (
          <span
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
            title={`Agents: ${liveAgents.join(', ')}`}
          >
            agents {liveAgents.length}
          </span>
        ) : null}
        {streamingActive && liveTool ? (
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${liveTool.status === 'running' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'bg-green-500/20 text-green-400 border border-green-500/30'}`}
            title={liveTool.status === 'running' ? 'Tool running' : 'Tool finished'}
          >
            {liveTool.status === 'running' ? (
              <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
            ) : null}
            Tool: {liveTool.name} {liveTool.status === 'running' ? '(running…) ' : '(done)'}
          </span>
        ) : null}
        {!streamingActive && turnStats ? (
          <>
            {!!(turnStats.model && turnStats.model.length > 0) ||
            !!(
              turnStats.provider &&
              (turnStats.token_in != null ||
                turnStats.token_out != null ||
                turnStats.cost_usd != null)
            ) ? (
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
                title="Model used"
              >
                {turnStats.provider
                  ? `${turnStats.provider}${turnStats.model ? ':' + turnStats.model : ''}`
                  : turnStats.model || ''}
              </span>
            ) : null}
            {turnStats.token_in != null || turnStats.token_out != null ? (
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
                title="Prompt/Completion tokens"
              >
                tokens {turnStats.token_in ?? 0}/{turnStats.token_out ?? 0}
              </span>
            ) : null}
            {turnStats.cost_usd != null ? (
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
                title="Estimated cost"
              >
                ${String(turnStats.cost_usd)}
              </span>
            ) : null}
            {turnStats.api_calls != null ? (
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
                title="API calls"
              >
                calls {turnStats.api_calls}
              </span>
            ) : null}
            {Array.isArray(turnStats.agents) && turnStats.agents.length ? (
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
                title={`Agents: ${turnStats.agents.join(', ')}`}
              >
                agents {turnStats.agents.length}
              </span>
            ) : null}
            {Array.isArray(turnStats.tools) && turnStats.tools.length ? (
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20"
                title={`Tools: ${turnStats.tools.join(', ')}`}
              >
                tools {turnStats.tools.length}
              </span>
            ) : null}
          </>
        ) : null}
      </div>
      <div className="flex gap-2 items-center">
        {currentId && typeof currentId === 'number' && <SummaryIndicator threadId={currentId} />}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => useHelp.getState().openHelp()}
          aria-label="Open keyboard shortcuts"
        >
          Help
        </Button>
        {streamingActive ? (
          <Button variant="ghost" size="sm" onClick={stop} aria-label="Stop streaming">
            Stop
          </Button>
        ) : null}
        <AuthControls />
        <SettingsButton />
        <HeaderOverflowMenu actions={headerActions} />
      </div>
      <ExportThreadModal open={exportOpen} onOpenChange={setExportOpen} threadId={currentId} />
    </div>
  )
}
