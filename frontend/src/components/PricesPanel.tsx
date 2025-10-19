import React, { useMemo, useState, lazy, Suspense } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { useTheme } from '../stores/settingsStore'
import { Sparkline } from './Sparkline'
import { AlertDetailModal } from './AlertDetailModal'
import { useProducts } from '../hooks/useProducts'
import { useIncidents, type Incident } from '../hooks/useIncidents'
import { usePriceStream } from '../hooks/usePriceStream'

const PriceChart = lazy(() => import('./PriceChart').then((m) => ({ default: m.PriceChart })))

const SEVERITY_CONFIG = {
  info: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Info', icon: 'ℹ️' },
  warn: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Warning', icon: '⚠️' },
  crit: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Critical', icon: '🚨' },
}

const PriceCardComponent = ({
  k,
  data,
  viewMode,
  theme,
  alert,
  onAlertClick,
  onAcknowledge,
  onResolve,
}: {
  k: string
  data: { ts: number; price: number }[]
  viewMode: 'sparkline' | 'chart'
  theme: 'dark' | 'light'
  alert?: Incident
  onAlertClick?: (alert: Incident) => void
  onAcknowledge?: (id: string) => void
  onResolve?: (id: string) => void
}) => {
  const vals = data.map((x) => x.price)
  const last = vals[vals.length - 1]
  const first = vals[0]
  const change = last && first ? ((last - first) / first) * 100 : 0
  const changeColor = change >= 0 ? '#10b981' : '#ef4444'
  const severity = alert ? SEVERITY_CONFIG[alert.severity] : null
  const isLLM = alert?.rule_id === 'llm_agent'

  return (
    <div
      key={k}
      className={`border rounded-lg p-3 bg-muted/30 transition-colors hover:bg-muted/50 ${
        alert ? `border-2 ${severity?.text.replace('text-', 'border-')}` : ''
      }`}
    >
      <div
        className={`flex justify-between items-center ${viewMode === 'chart' ? 'mb-3' : 'mb-2'}`}
      >
        <span className="font-medium text-sm">{k}</span>
        <div className="text-right">
          <div className="tabular-nums text-base font-semibold">${last?.toFixed?.(2) ?? '-'}</div>
          {viewMode === 'chart' && change !== 0 ? (
            <div className="text-[11px] font-medium" style={{ color: changeColor }}>
              {change > 0 ? '+' : ''}
              {change.toFixed(2)}%
            </div>
          ) : null}
        </div>
      </div>
      {viewMode === 'sparkline' ? (
        <Sparkline values={vals} />
      ) : (
        <Suspense
          fallback={<div className="text-center py-4 text-muted-foreground text-sm">Loading chart…</div>}
        >
          <PriceChart data={data} sku={k} theme={theme} />
        </Suspense>
      )}
      {alert && (
        <div className={`mt-3 pt-3 border-t ${severity?.text.replace('text-', 'border-')}`}>
          <div className="flex items-start gap-2 mb-2">
            <span className="text-base">{severity?.icon}</span>
            <div className="flex-1">
              <div className="font-semibold text-xs">{alert.title}</div>
              {isLLM && (
                <div className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-purple-500/30 text-purple-300 text-[10px] font-medium border border-purple-400/30 mt-1">
                  <span>🤖</span>
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
  const [collapsed, setCollapsed] = useState(localStorage.getItem('pricesCollapsed') === '1')
  const [running, setRunning] = useState(true)
  const [sku, setSku] = useState('')
  const [viewMode, setViewMode] = useState<'sparkline' | 'chart'>('sparkline')
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const theme = useTheme()

  const { products } = useProducts()
  const { incidents, acknowledgeIncident, resolveIncident } = useIncidents()
  const prices = usePriceStream(running, sku)

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
      className={`${collapsed ? 'w-12' : 'w-[280px]'} border-l p-4 overflow-auto transition-all duration-300`}
      aria-label="Prices panel"
    >
      <div className="flex gap-2 items-center mb-2">
        <Button
          variant="ghost"
          size="icon"
          aria-label={collapsed ? 'Expand prices panel' : 'Collapse prices panel'}
          onClick={() =>
            setCollapsed((c) => {
              const n = !c
              localStorage.setItem('pricesCollapsed', n ? '1' : '0')
              return n
            })
          }
          aria-expanded={!collapsed}
        >
          {collapsed ? '⮞' : '⮜'}
        </Button>
        {!collapsed ? <strong>Prices</strong> : null}
        {!collapsed ? (
          <>
            <Input
              placeholder="sku (optional)"
              value={sku}
              onChange={(e) => setSku(e.target.value)}
              className="flex-1"
            />
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setViewMode((v) => (v === 'sparkline' ? 'chart' : 'sparkline'))}
              aria-label={
                viewMode === 'sparkline' ? 'Switch to chart view' : 'Switch to sparkline view'
              }
              title={viewMode === 'sparkline' ? 'Chart view' : 'Sparkline view'}
            >
              {viewMode === 'sparkline' ? '📊' : '📈'}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setRunning((r) => !r)}
              aria-label={running ? 'Pause stream' : 'Resume stream'}
            >
              {running ? '⏸' : '▶'}
            </Button>
          </>
        ) : null}
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
                  const severity = SEVERITY_CONFIG[incident.severity]
                  const isLLM = incident.rule_id === 'llm_agent'
                  return (
                    <div
                      key={incident.id}
                      className={`p-3 rounded-lg border-2 ${severity.bg} ${severity.text} border-current/40`}
                    >
                      <div className="flex items-start gap-2 mb-2">
                        <span className="text-base">{severity.icon}</span>
                        <div className="flex-1">
                          <div className="font-semibold text-xs">{incident.title}</div>
                          <div className="text-[10px] text-muted-foreground mt-0.5">
                            SKU: {incident.sku}
                          </div>
                          {isLLM && (
                            <div className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-purple-500/30 text-purple-300 text-[10px] font-medium border border-purple-400/30 mt-1">
                              <span>🤖</span>
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
            <div className="text-center py-12 px-6 text-muted-foreground text-sm">Waiting for prices…</div>
          ) : null}
          {keys.map((k) => (
            <PriceCard
              key={k}
              k={k}
              data={prices[k] || []}
              viewMode={viewMode}
              theme={theme}
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
    </aside>
  )
}
