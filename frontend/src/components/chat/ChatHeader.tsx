import { useMemo, useState, useEffect, useRef } from 'react'
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
import { ExportThreadModal } from './ExportThreadModal'
import { useSidebar } from '../../stores/sidebarStore'
import { usePanels } from '../../stores/panelsStore'
import { Menu, BarChart3 } from 'lucide-react'

export function ChatHeader() {
  const { stop } = useMessagesActions()
  const { streamingActive, liveActiveAgent, liveTool, liveAgents, turnStats } = useStreamingState()
  const currentId = useCurrentThread()
  const [exportOpen, setExportOpen] = useState(false)
  const { collapsed } = useSidebar()
  const { pricesCollapsed } = usePanels()
  const leftToggleRef = useRef<HTMLButtonElement>(null)
  const rightToggleRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    const isMobile = window.matchMedia('(max-width: 767px)').matches
    if (!collapsed && isMobile) {
      const firstElement = document.querySelector<HTMLElement>(
        '#sidebar [tabindex], #sidebar button, #sidebar a'
      )
      firstElement?.focus()
    } else if (collapsed) {
      leftToggleRef.current?.focus()
    }
  }, [collapsed])

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    const isMobile = window.matchMedia('(max-width: 767px)').matches
    if (!pricesCollapsed && isMobile) {
      const firstElement = document.querySelector<HTMLElement>(
        '#prices-panel [tabindex], #prices-panel button, #prices-panel a'
      )
      firstElement?.focus()
    } else if (pricesCollapsed) {
      rightToggleRef.current?.focus()
    }
  }, [pricesCollapsed])

  const headerActions = useMemo<HeaderMenuAction[]>(
    () => [
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
  )

  const summaryThreadId = typeof currentId === 'number' ? currentId : undefined

  return (
    <div className="flex items-center gap-3 px-6 py-3 border-b justify-between bg-card/50 transition-[padding] duration-300 ease-in-out">
      <div className="flex gap-2 items-center flex-wrap min-w-0">
        <button
          ref={leftToggleRef}
          className="md:hidden inline-flex items-center justify-center p-2 rounded border hover:bg-muted/50"
          aria-label="Toggle sidebar"
          aria-controls="sidebar"
          aria-expanded={!collapsed}
          onClick={() => useSidebar.getState().toggleCollapsed()}
        >
          <Menu className="h-4 w-4" />
        </button>
        <button
          ref={rightToggleRef}
          className="md:hidden inline-flex items-center justify-center p-2 rounded border hover:bg-muted/50"
          aria-label="Toggle prices panel"
          aria-controls="prices-panel"
          aria-expanded={!pricesCollapsed}
          onClick={() => usePanels.getState().togglePricesCollapsed()}
        >
          <BarChart3 className="h-4 w-4" />
        </button>
        <strong className="truncate max-w-[200px] md:max-w-[400px]">
          {currentId
            ? useThreads.getState().threads.find((x) => x.id === currentId)?.title || 'Untitled Thread'
            : 'No Thread Selected'}
        </strong>
        {streamingActive ? (
          <span
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-accent/20 text-accent border border-accent/30 whitespace-nowrap overflow-hidden text-ellipsis max-w-[40vw] md:max-w-none"
            title="Model is streaming a reply"
            aria-live="polite"
          >
            <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
            Streaming…
          </span>
        ) : null}
        {streamingActive && liveActiveAgent ? (
          <span
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-purple-500/20 text-purple-400 border border-purple-500/30 whitespace-nowrap overflow-hidden text-ellipsis max-w-[40vw] md:max-w-none"
            title="Active agent"
          >
            Agent: {liveActiveAgent}
          </span>
        ) : null}
        {streamingActive && Array.isArray(liveAgents) && liveAgents.length ? (
          <span
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20 whitespace-nowrap overflow-hidden text-ellipsis max-w-[40vw] md:max-w-none"
            title={`Agents: ${liveAgents.join(', ')}`}
          >
            agents {liveAgents.length}
          </span>
        ) : null}
        {streamingActive && liveTool ? (
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap overflow-hidden text-ellipsis max-w-[40vw] md:max-w-none ${liveTool.status === 'running' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'bg-green-500/20 text-green-400 border border-green-500/30'}`}
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
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20 whitespace-nowrap overflow-hidden text-ellipsis max-w-[40vw] md:max-w-none"
                title="Model used"
              >
                {turnStats.provider
                  ? `${turnStats.provider}${turnStats.model ? ':' + turnStats.model : ''}`
                  : turnStats.model || ''}
              </span>
            ) : null}
            {turnStats.token_in != null || turnStats.token_out != null ? (
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20 whitespace-nowrap overflow-hidden text-ellipsis max-w-[40vw] md:max-w-none"
                title="Prompt/Completion tokens"
              >
                tokens {turnStats.token_in ?? 0}/{turnStats.token_out ?? 0}
              </span>
            ) : null}
            {turnStats.cost_usd != null ? (
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20 whitespace-nowrap overflow-hidden text-ellipsis max-w-[40vw] md:max-w-none"
                title="Estimated cost"
              >
                ${String(turnStats.cost_usd)}
              </span>
            ) : null}
            {turnStats.api_calls != null ? (
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20 whitespace-nowrap overflow-hidden text-ellipsis max-w-[40vw] md:max-w-none"
                title="API calls"
              >
                calls {turnStats.api_calls}
              </span>
            ) : null}
            {Array.isArray(turnStats.agents) && turnStats.agents.length ? (
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20 whitespace-nowrap overflow-hidden text-ellipsis max-w-[40vw] md:max-w-none"
                title={`Agents: ${turnStats.agents.join(', ')}`}
              >
                agents {turnStats.agents.length}
              </span>
            ) : null}
            {Array.isArray(turnStats.tools) && turnStats.tools.length ? (
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted/30 text-muted border border-muted/20 whitespace-nowrap overflow-hidden text-ellipsis max-w-[40vw] md:max-w-none"
                title={`Tools: ${turnStats.tools.join(', ')}`}
              >
                tools {turnStats.tools.length}
              </span>
            ) : null}
          </>
        ) : null}
      </div>
      <div className="flex gap-2 items-center">
        <SummaryIndicator threadId={summaryThreadId} />
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
      <ExportThreadModal open={exportOpen} onOpenChange={setExportOpen} threadId={typeof currentId === 'number' ? currentId : null} />
    </div>
  )
}
