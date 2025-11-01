import React, { useState } from 'react'
import { ChevronDown, ChevronRight, Bot } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface AgentActivityProps {
  agents?: { activated?: string[]; count?: number } | null
  tools?: { used?: string[]; count?: number } | null
}

export function AgentActivity({ agents, tools }: AgentActivityProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const agentNames = agents?.activated || []
  const agentCount = agents?.count ?? agentNames.length

  if (agentCount === 0 || agentNames.length === 0) {
    return null
  }

  const toolNames = tools?.used || []

  return (
    <div className="mt-2 border border-border/50 rounded-lg overflow-hidden bg-muted/30">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-2 px-3 py-2 text-xs text-muted-foreground hover:bg-muted/50 transition-colors"
        aria-expanded={isExpanded}
      >
        {isExpanded ? (
          <ChevronDown className="w-3 h-3" />
        ) : (
          <ChevronRight className="w-3 h-3" />
        )}
        <Bot className="w-3 h-3" />
        <span className="font-medium">
          Agent Activity ({agentCount} agent{agentCount !== 1 ? 's' : ''})
        </span>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-border/50"
          >
            <div className="px-3 py-2 space-y-2">
              <div className="space-y-1">
                {agentNames.map((agent, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-2 text-xs"
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-violet-500" />
                    <span className="text-foreground/80">{agent}</span>
                  </div>
                ))}
              </div>

              {toolNames.length > 0 && (
                <div className="pt-2 border-t border-border/30">
                  <div className="text-[10px] text-muted-foreground/70 mb-1">
                    Tools Used ({toolNames.length})
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {toolNames.map((tool, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] bg-primary/10 text-primary/80"
                      >
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
