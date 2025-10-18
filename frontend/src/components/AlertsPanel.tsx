import { useEffect, useState } from 'react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip'

interface Incident {
  id: string
  rule_id: string
  sku: string
  status: 'OPEN' | 'ACKED' | 'RESOLVED'
  first_seen: string
  last_seen: string
  severity: 'info' | 'warn' | 'crit'
  title: string
}

const SEVERITY_CONFIG = {
  info: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Info', icon: 'ℹ️' },
  warn: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Warning', icon: '⚠️' },
  crit: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Critical', icon: '🚨' },
}

const STATUS_CONFIG = {
  OPEN: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Open' },
  ACKED: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Acknowledged' },
  RESOLVED: { bg: 'bg-green-500/20', text: 'text-green-400', label: 'Resolved' },
}

export function AlertsPanel() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchIncidents = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/alerts/incidents')
      if (!response.ok) throw new Error('Failed to fetch incidents')
      const data = await response.json()
      setIncidents(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const acknowledgeIncident = async (incidentId: string) => {
    try {
      const response = await fetch(`/api/alerts/incidents/${incidentId}/ack`, { method: 'POST' })
      if (!response.ok) throw new Error('Failed to acknowledge incident')
      await fetchIncidents()
    } catch (err) {
      console.error('Error acknowledging incident:', err)
    }
  }

  const resolveIncident = async (incidentId: string) => {
    try {
      const response = await fetch(`/api/alerts/incidents/${incidentId}/resolve`, { method: 'POST' })
      if (!response.ok) throw new Error('Failed to resolve incident')
      await fetchIncidents()
    } catch (err) {
      console.error('Error resolving incident:', err)
    }
  }

  useEffect(() => {
    fetchIncidents()
    const interval = setInterval(fetchIncidents, 30000)
    return () => clearInterval(interval)
  }, [])

  const openIncidents = incidents.filter((i) => i.status === 'OPEN')
  const otherIncidents = incidents.filter((i) => i.status !== 'OPEN')

  if (loading && incidents.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-muted-foreground">
        Loading alerts...
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-32 text-red-400">
        Error: {error}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">
          Alerts {openIncidents.length > 0 && `(${openIncidents.length} open)`}
        </h3>
        <button
          onClick={fetchIncidents}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          Refresh
        </button>
      </div>

      {incidents.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground text-sm">
          No alerts found
        </div>
      ) : (
        <div className="space-y-3">
          {openIncidents.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Open Alerts
              </div>
              {openIncidents.map((incident) => (
                <IncidentCard
                  key={incident.id}
                  incident={incident}
                  onAcknowledge={acknowledgeIncident}
                  onResolve={resolveIncident}
                />
              ))}
            </div>
          )}

          {otherIncidents.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Recent Alerts
              </div>
              {otherIncidents.slice(0, 5).map((incident) => (
                <IncidentCard
                  key={incident.id}
                  incident={incident}
                  onAcknowledge={acknowledgeIncident}
                  onResolve={resolveIncident}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function IncidentCard({
  incident,
  onAcknowledge,
  onResolve,
}: {
  incident: Incident
  onAcknowledge: (id: string) => void
  onResolve: (id: string) => void
}) {
  const severity = SEVERITY_CONFIG[incident.severity]
  const status = STATUS_CONFIG[incident.status]
  const isLLM = incident.rule_id === 'llm_agent'

  return (
    <div
      className={`
        p-3 rounded-lg border-2 transition-all
        ${severity.bg} ${severity.text}
        ${incident.status === 'OPEN' ? 'border-current/40' : 'border-current/20 opacity-70'}
      `}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-base">{severity.icon}</span>
            <span className="font-semibold text-sm">{incident.title}</span>
            {isLLM && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-500/30 text-purple-300 text-xs font-medium border border-purple-400/30">
                      <span>🤖</span>
                      <span>AI</span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="top">
                    <div className="text-xs">
                      This alert was created by the AI Agent analyzing anomalies
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>

          <div className="flex items-center gap-3 text-xs">
            <span className={`px-2 py-0.5 rounded ${status.bg} ${status.text}`}>
              {status.label}
            </span>
            <span className="text-muted-foreground">SKU: {incident.sku}</span>
            <span className="text-muted-foreground">
              {new Date(incident.last_seen).toLocaleString()}
            </span>
          </div>
        </div>

        {incident.status === 'OPEN' && (
          <div className="flex items-center gap-1">
            <button
              onClick={() => onAcknowledge(incident.id)}
              className="px-2 py-1 text-xs rounded bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 transition-colors"
            >
              Ack
            </button>
            <button
              onClick={() => onResolve(incident.id)}
              className="px-2 py-1 text-xs rounded bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors"
            >
              Resolve
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
