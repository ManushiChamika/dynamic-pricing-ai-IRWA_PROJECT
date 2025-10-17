import { useMemo } from 'react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip'

const AGENT_COLORS: Record<string, { bg: string; text: string; icon: string }> = {
  UI: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: '👤' },
  Pricing: { bg: 'bg-purple-500/20', text: 'text-purple-400', icon: '🎯' },
  Data: { bg: 'bg-green-500/20', text: 'text-green-400', icon: '📊' },
  Alerts: { bg: 'bg-orange-500/20', text: 'text-orange-400', icon: '🔔' },
  UIA: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: '👤' },
  POA: { bg: 'bg-purple-500/20', text: 'text-purple-400', icon: '🎯' },
  DCA: { bg: 'bg-green-500/20', text: 'text-green-400', icon: '📊' },
  ANA: { bg: 'bg-orange-500/20', text: 'text-orange-400', icon: '🔔' },
  UserInteractionAgent: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: '👤' },
  PriceOptimizationAgent: { bg: 'bg-purple-500/20', text: 'text-purple-400', icon: '🎯' },
  DataCollectorAgent: { bg: 'bg-green-500/20', text: 'text-green-400', icon: '📊' },
  AlertNotificationAgent: { bg: 'bg-orange-500/20', text: 'text-orange-400', icon: '🔔' },
}

const AGENT_DESCRIPTIONS: Record<string, string> = {
  UI: 'User Interaction - Routes user requests and ensures safety',
  Pricing: 'Price Optimization - Main orchestrator for pricing decisions',
  Data: 'Data Collector - Gathers market and competitor data',
  Alerts: 'Alert & Notification - Monitors system and sends notifications',
  UIA: 'User Interaction Agent - Routes user requests and ensures safety',
  POA: 'Price Optimization Agent - Main orchestrator for pricing decisions',
  DCA: 'Data Collector Agent - Gathers market and competitor data',
  ANA: 'Alert & Notification Agent - Monitors system and sends notifications',
  UserInteractionAgent: 'User Interaction Agent - Routes user requests and ensures safety',
  PriceOptimizationAgent: 'Price Optimization Agent - Main orchestrator for pricing decisions',
  DataCollectorAgent: 'Data Collector Agent - Gathers market and competitor data',
  AlertNotificationAgent: 'Alert & Notification Agent - Monitors system and sends notifications',
}

function getAgentShortName(name: string): string {
  if (name.includes('UserInteraction') || name === 'UIA') return 'UIA'
  if (name.includes('PriceOptimization') || name === 'POA') return 'POA'
  if (name.includes('DataCollector') || name === 'DCA') return 'DCA'
  if (name.includes('AlertNotification') || name === 'ANA') return 'ANA'
  return name.slice(0, 3).toUpperCase()
}

interface AgentBadgeProps {
  name: string
  isActive?: boolean
  variant?: 'circle' | 'pill'
}

export function AgentBadge({ name, isActive = false, variant = 'pill' }: AgentBadgeProps) {
  const shortName = useMemo(() => getAgentShortName(name), [name])
  const config = AGENT_COLORS[shortName] ||
    AGENT_COLORS[name] || {
      bg: 'bg-gray-500/20',
      text: 'text-gray-400',
      icon: '🤖',
    }
  const description = AGENT_DESCRIPTIONS[shortName] || AGENT_DESCRIPTIONS[name] || `Agent: ${name}`

  if (variant === 'circle') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div
              className={`
                relative flex items-center justify-center w-8 h-8 rounded-full 
                ${config.bg} ${config.text} 
                border-2 transition-all duration-300 
                ${
                  isActive
                    ? 'border-current shadow-lg scale-110 animate-pulse'
                    : 'border-current/30'
                }
              `}
              aria-label={`${name} agent${isActive ? ' (active)' : ''}`}
            >
              <span className="text-base">{config.icon}</span>
              {isActive && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-current rounded-full animate-ping" />
              )}
            </div>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs">
            <div className="text-xs space-y-1">
              <div className="font-semibold">{shortName}</div>
              <div className="text-muted-foreground">{description}</div>
              {isActive && <div className="text-green-400">● Currently active</div>}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className={`
              inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium
              ${config.bg} ${config.text}
              border-2 transition-all duration-300
              ${isActive ? 'border-current shadow-lg shadow-current/50 agent-badge-active' : 'border-current/30 opacity-60'}
            `}
            aria-label={`${name} agent${isActive ? ' (active)' : ''}`}
          >
            <span>{config.icon}</span>
            <span>{shortName}</span>
            {isActive && (
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-current"></span>
              </span>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <div className="text-xs space-y-1">
            <div className="font-semibold">{shortName}</div>
            <div className="text-muted-foreground">{description}</div>
            {isActive && <div className="text-green-400">● Currently active</div>}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

export function AgentBadgeGroup({
  agents,
  activeAgent,
  variant = 'pill',
}: {
  agents: string[]
  activeAgent?: string | null
  variant?: 'circle' | 'pill'
}) {
  if (!agents.length) return null

  return (
    <div className="flex items-center gap-2 flex-wrap" aria-label="Active agents">
      {agents.map((agent) => (
        <AgentBadge key={agent} name={agent} isActive={agent === activeAgent} variant={variant} />
      ))}
    </div>
  )
}
