'use client'
import { useState, useEffect, useCallback } from 'react'
import { api } from './api'

export function useSSE() {
  const [data, setData] = useState<any>(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const url = api.streamUrl()
    let es: EventSource
    let retry: ReturnType<typeof setTimeout>

    function connect() {
      es = new EventSource(url)
      es.onopen = () => setConnected(true)
      es.onmessage = (e) => {
        try { setData(JSON.parse(e.data)) } catch {}
      }
      es.onerror = () => {
        setConnected(false)
        es.close()
        retry = setTimeout(connect, 5000)
      }
    }
    connect()
    return () => { es?.close(); clearTimeout(retry) }
  }, [])

  return { data, connected }
}

export function useBotStatus() {
  const [status, setStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const refetch = useCallback(async () => {
    try {
      const d = await api.status()
      setStatus(d)
    } catch {} finally { setLoading(false) }
  }, [])

  useEffect(() => { refetch() }, [refetch])
  return { status, loading, refetch }
}

export function useTrades(limit = 50, strategy?: string) {
  const [trades, setTrades] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.trades(limit, strategy)
      .then(d => setTrades(d.trades || []))
      .catch(() => {})
      .finally(() => setLoading(false))
    const t = setInterval(() => {
      api.trades(limit, strategy).then(d => setTrades(d.trades || [])).catch(() => {})
    }, 15000)
    return () => clearInterval(t)
  }, [limit, strategy])

  return { trades, loading }
}

export function usePoints() {
  const [data, setData] = useState<any>(null)
  useEffect(() => {
    api.points().then(setData).catch(() => {})
    const t = setInterval(() => api.points().then(setData).catch(() => {}), 30000)
    return () => clearInterval(t)
  }, [])
  return data
}

export function useAirdrop() {
  const [data, setData] = useState<any>(null)
  useEffect(() => {
    api.airdrop().then(setData).catch(() => {})
    const t = setInterval(() => api.airdrop().then(setData).catch(() => {}), 30000)
    return () => clearInterval(t)
  }, [])
  return data
}
