import React, { useEffect, useMemo, useRef, useState, lazy, Suspense } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { useAutoAnimate } from '@formkit/auto-animate/react'
import { useTheme } from '../stores/settingsStore'
import { Sparkline } from './Sparkline'
import { useAuthToken } from '../stores/authStore'

const PriceChart = lazy(() => import('./PriceChart').then((m) => ({ default: m.PriceChart })))

export function PricesPanel() {
  const [collapsed, setCollapsed] = useState(localStorage.getItem('pricesCollapsed') === '1')
  const [running, setRunning] = useState(true)
  const [sku, setSku] = useState('')
  const [prices, setPrices] = useState<Record<string, { ts: number; price: number }[]>>({})
  const [viewMode, setViewMode] = useState<'sparkline' | 'chart'>('sparkline')
  const esRef = useRef<EventSource | null>(null)
  const [pricesParent] = useAutoAnimate()
  const theme = useTheme()
  const token = useAuthToken()

  useEffect(() => {
    if (!running || !token) {
      if (esRef.current) {
        try {
          esRef.current.close()
        } catch {
          /* ignore */
        }
        esRef.current = null
      }
      return
    }
    try {
      const url = new URL('/api/prices/stream', window.location.origin)
      const s = sku.trim()
      if (s) url.searchParams.set('sku', s)
      url.searchParams.set('token', token)
      const es = new EventSource(url.toString())
      esRef.current = es
      const onPrice = (e: MessageEvent) => {
        try {
          const data = JSON.parse((e as any).data || '{}')
          const key = data.sku || 'SKU'
          const p = Number(data.price)
          const ts = Number(data.ts) || Date.now()
          setPrices((prev) => {
            const list = (prev[key] || []).concat({ ts, price: p }).slice(-50)
            return { ...prev, [key]: list }
          })
        } catch {
          /* ignore invalid JSON */
        }
      }
      const onError = () => {
        /* keep open; server may retry */
      }
      es.addEventListener('price', onPrice as any)
      es.addEventListener('error', onError as any)
      return () => {
        try {
          es.close()
        } catch {
          /* ignore */
        }
        if (esRef.current === es) esRef.current = null
      }
    } catch {
      // ignore
    }
  }, [running, sku, token])

  const keys = useMemo(() => Object.keys(prices).sort(), [prices])

  return (
    <aside
      className={`${collapsed ? 'w-12' : 'w-[280px]'} border-l border-border p-[var(--space-4)] overflow-auto bg-[rgba(17,24,39,0.85)] backdrop-blur-3xl transition-all duration-300`}
      aria-label="Prices panel"
    >
      <div className="flex gap-[var(--space-2)] items-center mb-[var(--space-2)]">
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
        <div ref={pricesParent as any} className="grid gap-2">
          {keys.length === 0 ? (
            <div className="text-center py-12 px-6 text-muted text-base">Waiting for prices…</div>
          ) : null}
          {keys.map((k) => {
            const data = prices[k] || []
            const vals = data.map((x) => x.price)
            const last = vals[vals.length - 1]
            const first = vals[0]
            const change = last && first ? ((last - first) / first) * 100 : 0
            const changeColor = change >= 0 ? '#10b981' : '#ef4444'

            return (
              <div
                key={k}
                className="border border-border rounded-2xl p-4 bg-panel backdrop-blur-xl shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
              >
                <div
                  className={`flex justify-between items-center ${viewMode === 'chart' ? 'mb-3' : 'mb-2'}`}
                >
                  <span className="opacity-90 font-medium text-sm">{k}</span>
                  <div className="text-right">
                    <div className="tabular-nums text-base font-semibold">
                      ${last?.toFixed?.(2) ?? '-'}
                    </div>
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
                    fallback={
                      <div className="text-center py-4 text-muted text-sm">Loading chart…</div>
                    }
                  >
                    <PriceChart data={data} sku={k} theme={theme} />
                  </Suspense>
                )}
              </div>
            )
          })}
        </div>
      ) : null}
    </aside>
  )
}


