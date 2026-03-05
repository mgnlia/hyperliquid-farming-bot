'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Status {
  status: string
  simulation_mode: boolean
  portfolio_value: number
  cash: number
  realized_pnl: number
  unrealized_pnl: number
  defi_earned: number
  total_points: number
  airdrop_score: number
  risk_metrics: {
    peak_value: number
    current_drawdown: number
    is_halted: boolean
  }
}

interface Position {
  symbol?: string
  protocol?: string
  pool?: string
  side?: string
  size?: number
  entry_price?: number
  current_price?: number
  unrealized_pnl?: number
  deposited?: number
  apy?: number
  earned?: number
}

interface PointEntry {
  protocol: string
  points: number
  multiplier: number
  actions_count: number
}

interface SSEEvent {
  type: string
  timestamp: number
  [key: string]: unknown
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-hype-card border border-hype-border rounded-xl p-4">
      <div className="text-xs text-gray-500 uppercase tracking-wider">{label}</div>
      <div className="text-2xl font-bold mt-1 text-white">{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  )
}

function AirdropMeter({ score }: { score: number }) {
  const pct = Math.min(100, Math.max(0, score))
  const color = pct > 70 ? 'bg-hype-green' : pct > 40 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="bg-hype-card border border-hype-border rounded-xl p-4">
      <div className="text-xs text-gray-500 uppercase tracking-wider">Airdrop Score</div>
      <div className="text-3xl font-bold mt-1 text-hype-green">{pct.toFixed(1)}</div>
      <div className="w-full bg-gray-800 rounded-full h-3 mt-3">
        <div className={`${color} h-3 rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [status, setStatus] = useState<Status | null>(null)
  const [positions, setPositions] = useState<{ perps: Position[]; defi: Position[] }>({ perps: [], defi: [] })
  const [points, setPoints] = useState<PointEntry[]>([])
  const [events, setEvents] = useState<SSEEvent[]>([])
  const [connected, setConnected] = useState(false)
  const evtRef = useRef<EventSource | null>(null)

  const fetchData = useCallback(async () => {
    try {
      const [sRes, pRes, ptRes] = await Promise.all([
        fetch(`${API}/api/status`),
        fetch(`${API}/api/positions`),
        fetch(`${API}/api/points`),
      ])
      if (sRes.ok) setStatus(await sRes.json())
      if (pRes.ok) setPositions(await pRes.json())
      if (ptRes.ok) {
        const d = await ptRes.json()
        setPoints(d.breakdown || [])
      }
    } catch {
      /* API not available */
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 3000)
    return () => clearInterval(interval)
  }, [fetchData])

  useEffect(() => {
    const es = new EventSource(`${API}/api/stream`)
    evtRef.current = es
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as SSEEvent
        setEvents((prev) => [...prev.slice(-99), data])
        setConnected(true)
      } catch {
        /* parse error */
      }
    }
    es.onerror = () => setConnected(false)
    return () => es.close()
  }, [])

  const controlAgent = async (action: string) => {
    await fetch(`${API}/api/agent/${action}`, { method: 'POST' })
    setTimeout(fetchData, 500)
  }

  const pnlColor = (v: number) => (v >= 0 ? 'text-hype-green' : 'text-red-400')

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">
            <span className="text-hype-green">⚡</span> Hyperliquid Farming Bot
          </h1>
          <p className="text-gray-500 text-sm mt-1">HyperEVM Airdrop Farmer — $HYPE Season 3</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`inline-block w-2 h-2 rounded-full ${status?.status === 'running' ? 'bg-hype-green animate-pulse' : status?.status === 'halted' ? 'bg-red-500' : 'bg-gray-500'}`} />
          <span className="text-sm text-gray-400 capitalize">{status?.status || 'loading'}</span>
          {status?.simulation_mode && (
            <span className="text-xs bg-yellow-900/50 text-yellow-400 px-2 py-0.5 rounded">SIMULATION</span>
          )}
          <button onClick={() => controlAgent('start')} className="px-3 py-1 bg-hype-green/20 text-hype-green rounded text-sm hover:bg-hype-green/30">Start</button>
          <button onClick={() => controlAgent('stop')} className="px-3 py-1 bg-red-500/20 text-red-400 rounded text-sm hover:bg-red-500/30">Stop</button>
          <button onClick={() => controlAgent('resume')} className="px-3 py-1 bg-hype-blue/20 text-hype-blue rounded text-sm hover:bg-hype-blue/30">Resume</button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Portfolio Value" value={`$${(status?.portfolio_value || 0).toLocaleString()}`} />
        <StatCard label="Realized P&L" value={`$${(status?.realized_pnl || 0).toFixed(2)}`} sub={status?.realized_pnl !== undefined ? (status.realized_pnl >= 0 ? '↑' : '↓') : ''} />
        <StatCard label="Total Points" value={(status?.total_points || 0).toLocaleString()} />
        <AirdropMeter score={status?.airdrop_score || 0} />
      </div>

      {/* Positions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Perp Positions */}
        <div className="bg-hype-card border border-hype-border rounded-xl p-4">
          <h2 className="text-lg font-semibold mb-3 text-white">Perp Positions</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs uppercase">
                  <th className="text-left py-2">Symbol</th>
                  <th className="text-left py-2">Side</th>
                  <th className="text-right py-2">Size</th>
                  <th className="text-right py-2">Entry</th>
                  <th className="text-right py-2">Current</th>
                  <th className="text-right py-2">PnL</th>
                </tr>
              </thead>
              <tbody>
                {positions.perps.length === 0 ? (
                  <tr><td colSpan={6} className="text-center py-4 text-gray-600">No open positions</td></tr>
                ) : positions.perps.map((p, i) => (
                  <tr key={i} className="border-t border-hype-border">
                    <td className="py-2 font-mono">{p.symbol}</td>
                    <td className={`py-2 ${p.side === 'long' ? 'text-hype-green' : 'text-red-400'}`}>{p.side}</td>
                    <td className="py-2 text-right">{p.size?.toFixed(4)}</td>
                    <td className="py-2 text-right">${p.entry_price?.toFixed(2)}</td>
                    <td className="py-2 text-right">${p.current_price?.toFixed(2)}</td>
                    <td className={`py-2 text-right ${pnlColor(p.unrealized_pnl || 0)}`}>${(p.unrealized_pnl || 0).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* DeFi Positions */}
        <div className="bg-hype-card border border-hype-border rounded-xl p-4">
          <h2 className="text-lg font-semibold mb-3 text-white">DeFi Positions</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs uppercase">
                  <th className="text-left py-2">Protocol</th>
                  <th className="text-left py-2">Pool</th>
                  <th className="text-right py-2">Deposited</th>
                  <th className="text-right py-2">APY</th>
                  <th className="text-right py-2">Earned</th>
                </tr>
              </thead>
              <tbody>
                {positions.defi.length === 0 ? (
                  <tr><td colSpan={5} className="text-center py-4 text-gray-600">No DeFi positions</td></tr>
                ) : positions.defi.map((p, i) => (
                  <tr key={i} className="border-t border-hype-border">
                    <td className="py-2 text-hype-purple">{p.protocol}</td>
                    <td className="py-2">{p.pool}</td>
                    <td className="py-2 text-right">${p.deposited?.toFixed(2)}</td>
                    <td className="py-2 text-right text-hype-green">{((p.apy || 0) * 100).toFixed(1)}%</td>
                    <td className="py-2 text-right text-hype-green">${(p.earned || 0).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Points Tracker */}
      <div className="bg-hype-card border border-hype-border rounded-xl p-4 mb-8">
        <h2 className="text-lg font-semibold mb-3 text-white">Points Tracker</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {points.map((p) => (
            <div key={p.protocol} className="bg-hype-dark rounded-lg p-3 text-center">
              <div className="text-xs text-gray-500">{p.protocol}</div>
              <div className="text-xl font-bold text-white mt-1">{p.points.toFixed(0)}</div>
              <div className="text-xs text-hype-green mt-1">{p.multiplier.toFixed(1)}x</div>
              <div className="text-xs text-gray-600">{p.actions_count} actions</div>
            </div>
          ))}
        </div>
      </div>

      {/* Event Feed */}
      <div className="bg-hype-card border border-hype-border rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-white">Live Events</h2>
          <span className={`text-xs ${connected ? 'text-hype-green' : 'text-red-400'}`}>
            {connected ? '● Connected' : '○ Disconnected'}
          </span>
        </div>
        <div className="space-y-1 max-h-64 overflow-y-auto font-mono text-xs">
          {events.length === 0 ? (
            <div className="text-gray-600 text-center py-4">No events yet — start the agent</div>
          ) : events.slice().reverse().map((e, i) => (
            <div key={i} className="flex gap-2 py-1 border-b border-hype-border/50">
              <span className="text-gray-600">{new Date(e.timestamp * 1000).toLocaleTimeString()}</span>
              <span className={
                e.type === 'points_earned' ? 'text-hype-purple' :
                e.type === 'open' ? 'text-hype-blue' :
                e.type === 'close' ? 'text-yellow-400' :
                e.type === 'defi_deposit' ? 'text-hype-green' :
                e.type === 'risk_halt' ? 'text-red-500' :
                'text-gray-400'
              }>[{e.type}]</span>
              <span className="text-gray-300 truncate">
                {e.type === 'points_earned' && `${e.protocol}: +${e.points} pts (${e.action})`}
                {e.type === 'open' && `${e.symbol} ${e.side} @ $${e.price}`}
                {e.type === 'close' && `${e.symbol} PnL: $${e.pnl}`}
                {e.type === 'defi_deposit' && `${e.protocol} ${e.pool}: $${e.amount}`}
                {e.type === 'status_update' && `Portfolio: $${e.portfolio_value} | Points: ${e.total_points}`}
                {e.type === 'risk_halt' && `Drawdown limit reached: ${((e.drawdown as number) * 100).toFixed(1)}%`}
                {e.type === 'agent_started' && `Agent started with $${e.portfolio_value}`}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-xs text-gray-600 mt-8 pb-4">
        Hyperliquid HyperEVM Farming Bot • Simulation Mode • Not Financial Advice
      </div>
    </main>
  )
}
