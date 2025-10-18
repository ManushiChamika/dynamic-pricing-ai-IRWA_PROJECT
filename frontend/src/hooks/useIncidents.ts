import { useCallback, useEffect, useState } from 'react'
import { useAuthToken } from '../stores/authStore'

export interface Incident {
  id: string
  rule_id: string
  sku: string
  status: 'OPEN' | 'ACKED' | 'RESOLVED'
  first_seen: string
  last_seen: string
  severity: 'info' | 'warn' | 'crit'
  title: string
}

export function useIncidents() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const token = useAuthToken()

  const fetchIncidents = useCallback(async () => {
    if (!token) return
    try {
      const response = await fetch(`/api/alerts/incidents?token=${token}`)
      if (!response.ok) throw new Error('Failed to fetch incidents')
      const data = await response.json()
      setIncidents(data.filter((i: Incident) => i.status === 'OPEN' || i.status === 'ACKED'))
    } catch (err) {
      console.error('Error fetching incidents:', err)
    }
  }, [token])

  const acknowledgeIncident = useCallback(async (incidentId: string) => {
    if (!token) return
    try {
      const response = await fetch(`/api/alerts/incidents/${incidentId}/ack?token=${token}`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to acknowledge incident')
      await fetchIncidents()
    } catch (err) {
      console.error('Error acknowledging incident:', err)
    }
  }, [token, fetchIncidents])

  const resolveIncident = useCallback(async (incidentId: string) => {
    if (!token) return
    try {
      const response = await fetch(`/api/alerts/incidents/${incidentId}/resolve?token=${token}`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to resolve incident')
      await fetchIncidents()
    } catch (err) {
      console.error('Error resolving incident:', err)
    }
  }, [token, fetchIncidents])

  useEffect(() => {
    fetchIncidents()
    const interval = setInterval(fetchIncidents, 30000)
    return () => clearInterval(interval)
  }, [fetchIncidents])

  return {
    incidents,
    acknowledgeIncident,
    resolveIncident,
    refetch: fetchIncidents,
  }
}
