'use client'
import { useEffect, useState } from 'react'
import { getSSEUrl } from '@/lib/api'

interface BotState {
  bot_running: boolean
  simulation_mode: boolean
  daily_pnl: number
  risk: { allowed: boolean; reason: string }
  perp: { trade_count: number; total_volume_usd: number }
  defi: { farm_count: number; total_farm_volume_usd: number; protocols_used: string[] }
  stats: { total_trades: number; total_volume_usd: number; total_pnl: number; farm_events: number; total_points: number }
}

interface SSEData {
  ts: string
  bot_running: boolean
  stats: BotState['stats']
  points: number
  tier: string
}

const TIER_COLORS: Record<string, string> = {
  Bronze: 'text-orange-400',
  Silver: 'text-gray-300',
  Gold: 'text-yellow-400',
  Platinum: 'text-cyan-400',
  Diamond: 'text-purple-400',
}

export default function Dashboard() {
  const [status, setStatus] = useState<BotState | null>(null)
  const [sseData, setSseData] = useState<SSEData | null>(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch((process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/status')
      .then(r => r.json())
      .then(setStatus)
      .catch(e => setError(e.message))

    const es = new EventSource(getSSEUrl())
    es.onopen = () => setConnected(true)
    es.onmessage = (e) => {
      try { setSseData(JSON.parse(e.data)) } catch {}
    }
    es.onerror = () => setConnected(false)
    return () => es.close()
  }, [])

  const tierColor = sseData ? (TIER_COLORS[sseData.tier] || 'text-white') : 'text-white'

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-green-400">⚡ Hyperliquid Farming Bot</h1>
          <p className="text-gray-400 mt-1">$HYPE Season 3 Airdrop Farming Dashboard</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`w-3 h-3 rounded-full ${connected ? 'bg-green-400 animate-pulse' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-400">{connected ? 'Live' : 'Disconnected'}</span>
          {status?.simulation_mode && (
            <span className="bg-yellow-900 text-yellow-300 text-xs px-2 py-1 rounded">SIMULATION</span>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-500 rounded p-4 text-red-300">
          Backend not connected: {error}. Set NEXT_PUBLIC_API_URL env var.
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Trades" value={String(sseData?.stats.total_trades ?? status?.stats.total_trades ?? 0)} />
        <StatCard label="Total Volume" value={`$${((sseData?.stats.total_volume_usd ?? status?.stats.total_volume_usd ?? 0)).toFixed(2)}`} />
        <StatCard label="Total P&L" value={`$${((sseData?.stats.total_pnl ?? status?.stats.total_pnl ?? 0)).toFixed(4)}`} />
        <StatCard label="Farm Events" value={String(sseData?.stats.farm_events ?? status?.stats.farm_events ?? 0)} />
      </div>

      {/* Airdrop Score */}
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
        <h2 className="text-xl font-semibold mb-4">🏆 Airdrop Score</h2>
        <div className="flex items-center gap-8">
          <div className="text-center">
            <div className={`text-5xl font-bold ${tierColor}`}>{sseData?.tier ?? '—'}</div>
            <div className="text-gray-400 text-sm mt-1">Current Tier</div>
          </div>
          <div className="flex-1">
            <div className="text-3xl font-bold text-white">{(sseData?.points ?? 0).toFixed(2)}</div>
            <div className="text-gray-400 text-sm">Estimated Points</div>
            <div className="mt-3 bg-gray-800 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-green-500 to-cyan-400 h-3 rounded-full transition-all"
                style={{ width: `${Math.min(((sseData?.points ?? 0) / 1000) * 100, 100)}%` }}
              />
            </div>
            <div className="text-xs text-gray-500 mt-1">Progress to Gold (1,000 pts)</div>
          </div>
        </div>
      </div>

      {/* Strategy Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
          <h3 className="font-semibold text-blue-400 mb-3">📈 Perp Trading</h3>
          <div className="space-y-2 text-sm">
            <Row label="Trades" value={String(status?.perp.trade_count ?? 0)} />
            <Row label="Volume" value={`$${(status?.perp.total_volume_usd ?? 0).toFixed(2)}`} />
            <Row label="Daily P&L" value={`$${(status?.daily_pnl ?? 0).toFixed(4)}`} />
          </div>
        </div>
        <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
          <h3 className="font-semibold text-purple-400 mb-3">🌾 DeFi Farming</h3>
          <div className="space-y-2 text-sm">
            <Row label="Farm Events" value={String(status?.defi.farm_count ?? 0)} />
            <Row label="Volume" value={`$${(status?.defi.total_farm_volume_usd ?? 0).toFixed(2)}`} />
            <Row label="Protocols" value={(status?.defi.protocols_used ?? []).join(', ') || '—'} />
          </div>
        </div>
      </div>

      {/* Risk Status */}
      {status?.risk && (
        <div className={`rounded-xl p-4 border ${status.risk.allowed ? 'bg-green-900/20 border-green-800' : 'bg-red-900/20 border-red-800'}`}>
          <span className="font-semibold">{status.risk.allowed ? '✅ Risk OK' : '🛑 Risk Blocked'}</span>
          <span className="text-gray-400 ml-3 text-sm">{status.risk.reason}</span>
        </div>
      )}

      <div className="text-center text-gray-600 text-xs">
        Last update: {sseData?.ts ? new Date(sseData.ts).toLocaleTimeString() : '—'}
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-gray-400 text-sm mt-1">{label}</div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-400">{label}</span>
      <span className="text-white">{value}</span>
    </div>
  )
}
