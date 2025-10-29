import React, { useMemo, useState } from 'react'
import { usePanels } from '../stores/panelsStore'
import { Button } from './ui/button'
import { Sparkline } from './Sparkline'
import { AlertDetailModal } from './AlertDetailModal'
import { useProducts } from '../hooks/useProducts'
import { useIncidents, type Incident } from '../hooks/useIncidents'
import { usePriceStream } from '../hooks/usePriceStream'
import {
  ChevronLeft,
  ChevronRight,
  Info,
  AlertTriangle,
  AlertCircle,
  Bot,
} from 'lucide-react'

const SEVERITY_CONFIG = {
  info: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Info', icon: Info },
  low: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Low', icon: Info },
  warn: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Warning', icon: AlertTriangle },
  medium: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Medium', icon: AlertTriangle },
  high: { bg: 'bg-orange-500/20', text: 'text-orange-400', label: 'High', icon: AlertCircle },
  crit: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Critical', icon: AlertCircle },
  critical: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Critical', icon: AlertCircle },
}

const PriceCardComponent = ({
  k,
  data,
  alert,
  onAlertClick,
  onAcknowledge,
  onResolve,
}: {
  k: string
  data: { ts: number; price: number }[]
  alert?: Incident
  onAlertClick?: (alert: Incident) => void
  onAcknowledge?: (id: string) => void
  onResolve?: (id: string) => void
}) => {
  const vals = data.map((x) => x.price)
  const last = vals[vals.length - 1]
  const severity = alert ? SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG['info'] : null
  const isLLM = alert?.rule_id === 'llm_agent'
  const SeverityIcon = severity?.icon

  return (
    <div
      key={k}
      className={`border rounded-lg p-3 bg-card/40 backdrop-blur-sm transition-colors hover:bg-card/60 ${
        alert ? `border-2 ${severity?.text.replace('text-', 'border-')}` : ''
      }`}
    >
      <div className="flex justify-between items-center mb-2">
        <span className="font-medium text-sm">{k}</span>
        <div className="text-right">
          <div className="tabular-nums text-base font-semibold">${last?.toFixed?.(2) ?? '-'}</div>
        </div>
      </div>
      <Sparkline values={vals} />
      {alert && (
        <div className={`mt-3 pt-3 border-t ${severity?.text.replace('text-', 'border-')}`}>
          <div className="flex items-start gap-2 mb-2">
            {SeverityIcon && <SeverityIcon className="h-4 w-4 mt-0.5" />}
            <div className="flex-1">
              <div className="font-semibold text-xs">{alert.title}</div>
              {isLLM && (
                <div className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-purple-500/30 text-purple-300 text-[10px] font-medium border border-purple-400/30 mt-1">
                  <Bot className="h-3 w-3" />
                  <span>AI</span>
                </div>
              )}
            </div>
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => onAlertClick?.(alert)}
              className="px-2 py-1 text-[10px] rounded bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors flex-1"
            >
              Details
            </button>
            {alert.status === 'OPEN' && (
              <>
                <button
                  onClick={() => onAcknowledge?.(alert.id)}
                  className="px-2 py-1 text-[10px] rounded bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 transition-colors flex-1"
                >
                  Ack
                </button>
                <button
                  onClick={() => onResolve?.(alert.id)}
                  className="px-2 py-1 text-[10px] rounded bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors flex-1"
                >
                  Resolve
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

const PriceCard = React.memo(PriceCardComponent)

export function PricesPanel() {
  const { pricesCollapsed, togglePricesCollapsed } = usePanels()
  const collapsed = pricesCollapsed
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  const { products } = useProducts()
  const { incidents, acknowledgeIncident, resolveIncident } = useIncidents()
  const prices = usePriceStream(true, '')

  const handleAlertClick = (incident: Incident) => {
    setSelectedIncident(incident)
    setModalOpen(true)
  }

  const keys = useMemo(() => {
    const priceKeys = Object.keys(prices)
    const allKeys = [...new Set([...priceKeys, ...products])]
    return allKeys.sort()
  }, [prices, products])

  const incidentsBySku = useMemo(() => {
    const map: Record<string, Incident> = {}
    incidents.forEach((inc) => {
      if (!map[inc.sku] || map[inc.sku].severity === 'info') {
        map[inc.sku] = inc
      }
    })
    return map
  }, [incidents])

  return (
    <aside
      id="prices-panel"
      className={`fixed inset-y-0 right-0 z-40 border-l transition-all duration-250 ease-in-out motion-reduce:transition-none ${collapsed ? 'w-12 p-2 bg-background/30 backdrop-blur-sm translate-x-full md:translate-x-0' : 'w-[280px] p-4 overflow-auto bg-muted/40 backdrop-blur translate-x-0'}`}
      aria-label="Prices panel"
    >
      <div
        className={`will-change-transform transition-transform duration-250 ease-in-out motion-reduce:transition-none`}
      >
        <div className={collapsed ? 'h-full flex items-center justify-center' : 'sticky top-0 z-10 bg-background/30 backdrop-blur-sm pb-2 flex gap-2 items-center mb-2'}>
          <Button
            variant="ghost"
            size="icon"
            aria-label={collapsed ? 'Expand prices panel' : 'Collapse prices panel'}
            onClick={togglePricesCollapsed}
            aria-expanded={!collapsed}
          >
            {collapsed ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
          {!collapsed ? <span className="text-sm font-semibold leading-none">Prices</span> : null}
        </div>
        {!collapsed ? (
          <div className="grid gap-2">
            {incidents.filter((i) => !incidentsBySku[i.sku] || keys.length === 0).length > 0 && (
              <div className="space-y-2 mb-4">
                <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Alerts
                </div>
                {incidents
                  .filter((i) => !incidentsBySku[i.sku] || keys.length === 0)
                  .map((incident) => {
                    const severity = SEVERITY_CONFIG[incident.severity] || SEVERITY_CONFIG['info']
                    const isLLM = incident.rule_id === 'llm_agent'
                    const IncidentIcon = severity.icon
                    return (
                      <div
                        key={incident.id}
                        className={`p-3 rounded-lg border-2 ${severity.bg} ${severity.text} border-current/40`}
                      >
                        <div className="flex items-start gap-2 mb-2">
                          <IncidentIcon className="h-4 w-4 mt-0.5" />
                          <div className="flex-1">
                            <div className="font-semibold text-xs">{incident.title}</div>
                            <div className="text-[10px] text-muted-foreground mt-0.5">
                              SKU: {incident.sku}
                            </div>
                            {isLLM && (
                              <div className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-purple-500/30 text-purple-300 text-[10px] font-medium border border-purple-400/30 mt-1">
                                <Bot className="h-3 w-3" />
                                <span>AI</span>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleAlertClick(incident)}
                            className="px-2 py-1 text-[10px] rounded bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors flex-1"
                          >
                            Details
                          </button>
                          {incident.status === 'OPEN' && (
                            <>
                              <button
                                onClick={() => acknowledgeIncident(incident.id)}
                                className="px-2 py-1 text-[10px] rounded bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 transition-colors flex-1"
                              >
                                Ack
                              </button>
                              <button
                                onClick={() => resolveIncident(incident.id)}
                                className="px-2 py-1 text-[10px] rounded bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors flex-1"
                              >
                                Resolve
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    )
                  })}
              </div>
            )}
            {keys.length === 0 && incidents.length === 0 ? (
              <div className="text-center py-12 px-6 text-muted-foreground text-sm">
                Waiting for prices…
              </div>
            ) : null}
            {keys.map((k) => (
              <PriceCard
                key={k}
                k={k}
                data={prices[k] || []}
                alert={incidentsBySku[k]}
                onAlertClick={handleAlertClick}
                onAcknowledge={acknowledgeIncident}
                onResolve={resolveIncident}
              />
            ))}
          </div>
        ) : null}
        <AlertDetailModal
          incident={selectedIncident}
          open={modalOpen}
          onOpenChange={setModalOpen}
          onAcknowledge={acknowledgeIncident}
          onResolve={resolveIncident}
        />
      </div>
    </aside>
  )
}
