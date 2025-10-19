import { useMemo } from 'react'
import { MessageSquare, TrendingUp, Database, Bell } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip'

const AGENT_COLORS: Record<string, { bg: string; text: string; icon: any }> = {
  UI: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: MessageSquare },
  Pricing: { bg: 'bg-purple-500/20', text: 'text-purple-400', icon: TrendingUp },
  Data: { bg: 'bg-green-500/20', text: 'text-green-400', icon: Database },
  Alerts: { bg: 'bg-orange-500/20', text: 'text-orange-400', icon: Bell },
  UIA: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: MessageSquare },
  POA: { bg: 'bg-purple-500/20', text: 'text-purple-400', icon: TrendingUp },
  DCA: { bg: 'bg-green-500/20', text: 'text-green-400', icon: Database },
  ANA: { bg: 'bg-orange-500/20', text: 'text-orange-400', icon: Bell },
  UserInteractionAgent: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: MessageSquare },
  PriceOptimizationAgent: { bg: 'bg-purple-500/20', text: 'text-purple-400', icon: TrendingUp },
  DataCollectorAgent: { bg: 'bg-green-500/20', text: 'text-green-400', icon: Database },
  AlertNotificationAgent: { bg: 'bg-orange-500/20', text: 'text-orange-400', icon: Bell },
}

const AGENT_DESCRIPTIONS: Record<string, string> = {
  UI: 'User Interaction - Routes user requests and ensures safety',
  Pricing: 'Price Optimization - Main orchestrator for pricing decisions',
  Data: 'Data Collector - Gathers market and competitor data',
  Alerts: 'Alert & Notification - Monitors system and sends notifications',
  UIA: 'User Interaction - Routes user requests and ensures safety',
  POA: 'Price Optimization - Main orchestrator for pricing decisions',
  DCA: 'Data Collector - Gathers market and competitor data',
  ANA: 'Alert & Notification - Monitors system and sends notifications',
  UserInteractionAgent: 'User Interaction - Routes user requests and ensures safety',
  PriceOptimizationAgent: 'Price Optimization - Main orchestrator for pricing decisions',
  DataCollectorAgent: 'Data Collector - Gathers market and competitor data',
  AlertNotificationAgent: 'Alert & Notification - Monitors system and sends notifications',
}

function getAgentDisplayName(name: string): string {
  if (name.includes('UserInteraction') || name === 'UIA' || name === 'UI') return 'User Interaction'
  if (name.includes('PriceOptimization') || name === 'POA' || name === 'Pricing') return 'Price Optimization'
  if (name.includes('DataCollector') || name === 'DCA' || name === 'Data') return 'Data Collector'
  if (name.includes('AlertNotification') || name === 'ANA' || name === 'Alerts') return 'Alert & Notification'
  return name
}

function getAgentKey(name: string): string {
  if (name.includes('UserInteraction') || name === 'UIA') return 'UIA'
  if (name.includes('PriceOptimization') || name === 'POA') return 'POA'
  if (name.includes('DataCollector') || name === 'DCA') return 'DCA'
  if (name.includes('AlertNotification') || name === 'ANA') return 'ANA'
  return name
}

interface AgentBadgeProps {
  name: string
  isActive?: boolean
  variant?: 'circle' | 'pill'
}

export function AgentBadge({ name, isActive = false, variant = 'pill' }: AgentBadgeProps) {
  const displayName = useMemo(() => getAgentDisplayName(name), [name])
  const agentKey = useMemo(() => getAgentKey(name), [name])
  const config = AGENT_COLORS[agentKey] ||
    AGENT_COLORS[name] || {
      bg: 'bg-gray-500/20',
      text: 'text-gray-400',
      icon: MessageSquare,
    }
  const description = AGENT_DESCRIPTIONS[agentKey] || AGENT_DESCRIPTIONS[name] || `Agent: ${name}`
  const IconComponent = config.icon

  if (variant === 'circle') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div
              className={`
                relative flex items-center justify-center w-10 h-10 rounded-full 
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
              <IconComponent className="w-5 h-5" />
              {isActive && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-current rounded-full animate-ping" />
              )}
            </div>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs">
            <div className="text-xs space-y-1">
              <div className="font-semibold">{displayName}</div>
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
            <IconComponent className="w-4 h-4" />
            <span>{displayName}</span>
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
            <div className="font-semibold">{displayName}</div>
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
