import { useEffect, useRef, useState } from 'react'
import { useAuthToken } from '../stores/authStore'

export function usePriceStream(running: boolean, sku: string) {
  const [prices, setPrices] = useState<Record<string, { ts: number; price: number }[]>>({})
  const esRef = useRef<EventSource | null>(null)
  const throttleRef = useRef<ReturnType<typeof setTimeout>>()
  const token = useAuthToken()

  useEffect(() => {
    if (!running || !token) {
      if (esRef.current) {
        try {
          esRef.current.close()
        } catch (err) {
          console.debug('Error closing EventSource:', err)
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

          if (throttleRef.current) clearTimeout(throttleRef.current)
          throttleRef.current = setTimeout(() => {
            setPrices((prev) => {
              const list = (prev[key] || []).concat({ ts, price: p }).slice(-50)
              return { ...prev, [key]: list }
            })
          }, 100)
        } catch (err) {
          console.debug('Error parsing price event:', err)
        }
      }
      const onError = () => {}
      es.addEventListener('price', onPrice as any)
      es.addEventListener('error', onError as any)
      return () => {
        try {
          es.close()
        } catch (err) {
          console.debug('Error closing EventSource in cleanup:', err)
        }
        if (esRef.current === es) esRef.current = null
        if (throttleRef.current) clearTimeout(throttleRef.current)
      }
    } catch (err) {
      console.error('Error initializing price stream:', err)
    }
  }, [running, sku, token])

  return prices
}
