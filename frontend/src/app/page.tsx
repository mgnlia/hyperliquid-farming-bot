'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface RiskMetrics {
  peak_value: number
  current_drawdown: number
  max_drawdown_pct?: number
  max_position_pct?: number
  kelly_fraction?: number
  is_halted: boolean
}

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
  risk_metrics: RiskMetrics
  started_at?: number | null
}

interface PerpPosition {
  symbol: string
  side: string
  size: number
  entry_price: number
  current_price: number
  unrealized_pnl: number
  notional?: number
  opened_at: number
}

interface DefiPosition {
  protocol: string
  pool: string
  deposited: number
  apy: number
  earned: number
  started_at: number
}

interface PositionsResponse {
  perps: PerpPosition[]
  defi: DefiPosition[]
}

interface PointEntry {
  protocol: string
  points: number
  multiplier: number
  actions_count: number
  last_action: number
}

interface PointsResponse {
  breakdown: PointEntry[]
  total_points: number
  airdrop_score: number
}

interface TradeEntry {
  type: string
  symbol?: string
  side?: string
  size?: number
  notional?: number
  price?: number
  entry_price?: number
  exit_price?: number
  pnl?: number
  timestamp: number
}

interface TradesResponse {
  trades: TradeEntry[]
}

interface FeedEvent {
  type: string
  timestamp: number
  protocol?: string
  earned?: number
  total?: number
  symbol?: string
  side?: string
  price?: number
  pnl?: number
  action?: string
  amount?: number
  pool?: string
  portfolio_value?: number
  total_points?: number
  drawdown?: number
  reason?: string
  simulation_mode?: boolean
}

interface PnlPoint {
  timestamp: number
  value: number
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-hype-border bg-hype-card p-4">
      <div className="text-xs uppercase tracking-wider text-gray-500">{label}</div>
      <div className="mt-1 text-2xl font-bold text-white">{value}</div>
      {sub ? <div className="mt-1 text-xs text-gray-400">{sub}</div> : null}
    </div>
  )
}

function AirdropMeter({ score }: { score: number }) {
  const pct = Math.min(100, Math.max(0, score))
  const color = pct > 70 ? 'bg-hype-green' : pct > 40 ? 'bg-yellow-500' : 'bg-red-500'

  return (
    <div className="rounded-xl border border-hype-border bg-hype-card p-4">
      <div className="text-xs uppercase tracking-wider text-gray-500">Airdrop Score</div>
      <div className="mt-1 text-3xl font-bold text-hype-green">{pct.toFixed(1)}</div>
      <div className="mt-3 h-3 w-full rounded-full bg-gray-800">
        <div className={`${color} h-3 rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function PnlChart({ points }: { points: PnlPoint[] }) {
  const path = useMemo(() => {
    if (points.length === 0) {
      return ''
    }

    const values = points.map((point) => point.value)
    const min = Math.min(...values)
    const max = Math.max(...values)
    const range = Math.max(1, max - min)

    return points
      .map((point, index) => {
        const x = (index / Math.max(1, points.length - 1)) * 100
        const y = 100 - ((point.value - min) / range) * 100
        return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
      })
      .join(' ')
  }, [points])

  const latest = points.at(-1)?.value ?? 0
  const first = points[0]?.value ?? latest
  const delta = latest - first

  return (
    <div className="rounded-xl border border-hype-border bg-hype-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">P&amp;L Chart</h2>
          <p className="text-xs text-gray-500">Recent simulated portfolio value</p>
        </div>
        <div className={`text-sm font-medium ${delta >= 0 ? 'text-hype-green' : 'text-red-400'}`}>
          {delta >= 0 ? '+' : ''}${delta.toFixed(2)}
        </div>
      </div>
      {path ? (
        <svg viewBox="0 0 100 100" className="h-48 w-full overflow-visible">
          <defs>
            <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00d395" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#00d395" stopOpacity="0.02" />
            </linearGradient>
          </defs>
          <path d={`${path} L 100 100 L 0 100 Z`} fill="url(#pnlGradient)" />
          <path d={path} fill="none" stroke="#00d395" strokeWidth="2.2" strokeLinecap="round" />
        </svg>
      ) : (
        <div className="flex h-48 items-center justify-center text-sm text-gray-600">Waiting for status samples…</div>
      )}
    </div>
  )
}

function formatEvent(event: FeedEvent): string {
  switch (event.type) {
    case 'points_farmed':
      return `${event.protocol ?? 'Protocol'} earned ${Number(event.earned ?? 0).toFixed(2)} points (total ${Number(
        event.total ?? 0,
      ).toFixed(2)})`
    case 'perp_open':
      return `${event.symbol ?? 'Asset'} ${event.side ?? 'trade'} opened @ $${Number(event.price ?? 0).toFixed(2)}`
    case 'perp_close':
      return `${event.symbol ?? 'Asset'} closed with PnL $${Number(event.pnl ?? 0).toFixed(2)}`
    case 'defi_rebalance':
      return `${event.protocol ?? 'Protocol'} ${event.action ?? 'rebalance'} ${event.pool ?? 'position'} for $${Number(
        event.amount ?? 0,
      ).toFixed(2)}`
    case 'status':
      return `Portfolio $${Number(event.portfolio_value ?? 0).toFixed(2)} • Points ${Number(event.total_points ?? 0).toFixed(0)}`
    case 'risk_halt':
      return `${event.reason ?? 'Risk halt'} (${(Number(event.drawdown ?? 0) * 100).toFixed(2)}% drawdown)`
    case 'agent_started':
      return `Agent started in ${event.simulation_mode ? 'simulation' : 'live'} mode`
    case 'agent_stopped':
      return 'Agent stopped'
    case 'heartbeat':
      return 'Heartbeat'
    default:
      return event.type
  }
}

export default function Dashboard() {
  const [status, setStatus] = useState<Status | null>(null)
  const [positions, setPositions] = useState<PositionsResponse>({ perps: [], defi: [] })
  const [points, setPoints] = useState<PointsResponse>({ breakdown: [], total_points: 0, airdrop_score: 0 })
  const [trades, setTrades] = useState<TradeEntry[]>([])
  const [events, setEvents] = useState<FeedEvent[]>([])
  const [history, setHistory] = useState<PnlPoint[]>([])
  const [connected, setConnected] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      const [statusRes, positionsRes, pointsRes, tradesRes] = await Promise.all([
        fetch(`${API}/api/status`),
        fetch(`${API}/api/positions`),
        fetch(`${API}/api/points`),
        fetch(`${API}/api/trades`),
      ])

      if (statusRes.ok) {
        const nextStatus = (await statusRes.json()) as Status
        setStatus(nextStatus)
        setHistory((prev) => {
          const next = [...prev, { timestamp: Date.now(), value: nextStatus.portfolio_value }]
          return next.slice(-40)
        })
      }

      if (positionsRes.ok) {
        setPositions((await positionsRes.json()) as PositionsResponse)
      }

      if (pointsRes.ok) {
        setPoints((await pointsRes.json()) as PointsResponse)
      }

      if (tradesRes.ok) {
        const payload = (await tradesRes.json()) as TradesResponse
        setTrades(payload.trades)
      }
    } catch {
      setConnected(false)
    }
  }, [])

  useEffect(() => {
    void fetchData()
    const interval = setInterval(() => {
      void fetchData()
    }, 3000)
    return () => clearInterval(interval)
  }, [fetchData])

  useEffect(() => {
    const source = new EventSource(`${API}/api/stream`)

    source.onmessage = (message) => {
      try {
        const event = JSON.parse(message.data) as FeedEvent
        setConnected(true)
        setEvents((prev) => [...prev.slice(-119), event])
        if (event.type === 'status' && typeof event.portfolio_value === 'number') {
          setHistory((prev) => [...prev.slice(-39), { timestamp: event.timestamp, value: event.portfolio_value ?? 0 }])
        }
      } catch {
        setConnected(false)
      }
    }

    source.onerror = () => {
      setConnected(false)
    }

    return () => {
      source.close()
    }
  }, [])

  const controlAgent = useCallback(async (action: 'start' | 'stop') => {
    await fetch(`${API}/api/agent/${action}`, { method: 'POST' })
    await fetchData()
  }, [fetchData])

  const perpsUnrealized = positions.perps.reduce((sum, position) => sum + position.unrealized_pnl, 0)
  const pnlClass = (value: number) => (value >= 0 ? 'text-hype-green' : 'text-red-400')

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">
            <span className="text-hype-green">⚡</span> Hyperliquid Farming Bot
          </h1>
          <p className="mt-1 text-sm text-gray-500">HyperEVM Airdrop Farmer — $HYPE Season 3</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              status?.status === 'running'
                ? 'animate-pulse bg-hype-green'
                : status?.status === 'halted'
                  ? 'bg-red-500'
                  : 'bg-gray-500'
            }`}
          />
          <span className="text-sm capitalize text-gray-400">{status?.status ?? 'loading'}</span>
          {status?.simulation_mode ? (
            <span className="rounded bg-yellow-900/50 px-2 py-0.5 text-xs text-yellow-400">SIMULATION</span>
          ) : null}
          <span className={`text-xs ${connected ? 'text-hype-green' : 'text-red-400'}`}>
            {connected ? '● SSE Connected' : '○ SSE Disconnected'}
          </span>
          <button
            onClick={() => void controlAgent('start')}
            className="rounded bg-hype-green/20 px-3 py-1 text-sm text-hype-green hover:bg-hype-green/30"
          >
            Start
          </button>
          <button
            onClick={() => void controlAgent('stop')}
            className="rounded bg-red-500/20 px-3 py-1 text-sm text-red-400 hover:bg-red-500/30"
          >
            Stop
          </button>
        </div>
      </div>

      <div className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Portfolio Value" value={`$${(status?.portfolio_value ?? 0).toLocaleString()}`} />
        <StatCard
          label="Realized P&L"
          value={`$${(status?.realized_pnl ?? 0).toFixed(2)}`}
          sub={`Unrealized: $${(status?.unrealized_pnl ?? 0).toFixed(2)}`}
        />
        <StatCard label="Total Points" value={(points.total_points ?? 0).toLocaleString()} sub={`DeFi earned: $${(status?.defi_earned ?? 0).toFixed(2)}`} />
        <AirdropMeter score={points.airdrop_score ?? 0} />
      </div>

      <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-[1.35fr_0.65fr]">
        <PnlChart points={history} />
        <div className="rounded-xl border border-hype-border bg-hype-card p-4">
          <h2 className="mb-3 text-lg font-semibold text-white">Risk & Summary</h2>
          <div className="space-y-3 text-sm text-gray-300">
            <div className="flex items-center justify-between">
              <span>Cash</span>
              <span>${(status?.cash ?? 0).toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Open perps P&amp;L</span>
              <span className={pnlClass(perpsUnrealized)}>${perpsUnrealized.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Current drawdown</span>
              <span>{((status?.risk_metrics.current_drawdown ?? 0) * 100).toFixed(2)}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Peak value</span>
              <span>${(status?.risk_metrics.peak_value ?? 0).toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Risk state</span>
              <span className={status?.risk_metrics.is_halted ? 'text-red-400' : 'text-hype-green'}>
                {status?.risk_metrics.is_halted ? 'Halted' : 'Healthy'}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-hype-border bg-hype-card p-4">
          <h2 className="mb-3 text-lg font-semibold text-white">Perp Positions</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase text-gray-500">
                  <th className="py-2 text-left">Symbol</th>
                  <th className="py-2 text-left">Side</th>
                  <th className="py-2 text-right">Size</th>
                  <th className="py-2 text-right">Entry</th>
                  <th className="py-2 text-right">Current</th>
                  <th className="py-2 text-right">PnL</th>
                </tr>
              </thead>
              <tbody>
                {positions.perps.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-4 text-center text-gray-600">
                      No open positions
                    </td>
                  </tr>
                ) : (
                  positions.perps.map((position) => (
                    <tr key={`${position.symbol}-${position.opened_at}`} className="border-t border-hype-border">
                      <td className="py-2 font-mono">{position.symbol}</td>
                      <td className={`py-2 ${position.side === 'long' ? 'text-hype-green' : 'text-red-400'}`}>
                        {position.side}
                      </td>
                      <td className="py-2 text-right">{position.size.toFixed(4)}</td>
                      <td className="py-2 text-right">${position.entry_price.toFixed(2)}</td>
                      <td className="py-2 text-right">${position.current_price.toFixed(2)}</td>
                      <td className={`py-2 text-right ${pnlClass(position.unrealized_pnl)}`}>
                        ${position.unrealized_pnl.toFixed(2)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="rounded-xl border border-hype-border bg-hype-card p-4">
          <h2 className="mb-3 text-lg font-semibold text-white">DeFi Positions</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase text-gray-500">
                  <th className="py-2 text-left">Protocol</th>
                  <th className="py-2 text-left">Pool</th>
                  <th className="py-2 text-right">Deposited</th>
                  <th className="py-2 text-right">APY</th>
                  <th className="py-2 text-right">Earned</th>
                </tr>
              </thead>
              <tbody>
                {positions.defi.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-gray-600">
                      No DeFi positions
                    </td>
                  </tr>
                ) : (
                  positions.defi.map((position) => (
                    <tr key={`${position.protocol}-${position.pool}`} className="border-t border-hype-border">
                      <td className="py-2 text-hype-purple">{position.protocol}</td>
                      <td className="py-2">{position.pool}</td>
                      <td className="py-2 text-right">${position.deposited.toFixed(2)}</td>
                      <td className="py-2 text-right text-hype-green">{(position.apy * 100).toFixed(1)}%</td>
                      <td className="py-2 text-right text-hype-green">${position.earned.toFixed(2)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="mb-8 rounded-xl border border-hype-border bg-hype-card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Points Tracker</h2>
          <div className="text-xs text-gray-500">Felix • Mizu • Drip • Hyperbeat</div>
        </div>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {points.breakdown.map((point) => (
            <div key={point.protocol} className="rounded-lg bg-hype-dark p-3 text-center">
              <div className="text-xs text-gray-500">{point.protocol}</div>
              <div className="mt-1 text-xl font-bold text-white">{point.points.toFixed(0)}</div>
              <div className="mt-1 text-xs text-hype-green">{point.multiplier.toFixed(2)}x multiplier</div>
              <div className="text-xs text-gray-600">{point.actions_count} actions</div>
            </div>
          ))}
        </div>
      </div>

      <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-hype-border bg-hype-card p-4">
          <h2 className="mb-3 text-lg font-semibold text-white">Trade Log</h2>
          <div className="max-h-80 overflow-y-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase text-gray-500">
                  <th className="py-2 text-left">Time</th>
                  <th className="py-2 text-left">Type</th>
                  <th className="py-2 text-left">Symbol</th>
                  <th className="py-2 text-right">Price</th>
                  <th className="py-2 text-right">PnL</th>
                </tr>
              </thead>
              <tbody>
                {trades.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-gray-600">
                      No trades yet
                    </td>
                  </tr>
                ) : (
                  [...trades].reverse().map((trade) => (
                    <tr key={`${trade.type}-${trade.timestamp}-${trade.symbol ?? 'na'}`} className="border-t border-hype-border">
                      <td className="py-2 text-gray-400">{new Date(trade.timestamp * 1000).toLocaleTimeString()}</td>
                      <td className="py-2">{trade.type}</td>
                      <td className="py-2 font-mono">{trade.symbol ?? '-'}</td>
                      <td className="py-2 text-right">${Number(trade.price ?? trade.exit_price ?? trade.entry_price ?? 0).toFixed(2)}</td>
                      <td className={`py-2 text-right ${pnlClass(Number(trade.pnl ?? 0))}`}>
                        ${Number(trade.pnl ?? 0).toFixed(2)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="rounded-xl border border-hype-border bg-hype-card p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Event Feed</h2>
            <span className={`text-xs ${connected ? 'text-hype-green' : 'text-red-400'}`}>
              {connected ? '● Connected' : '○ Disconnected'}
            </span>
          </div>
          <div className="max-h-80 space-y-1 overflow-y-auto font-mono text-xs">
            {events.length === 0 ? (
              <div className="py-4 text-center text-gray-600">No events yet — start the agent</div>
            ) : (
              [...events].reverse().map((event, index) => (
                <div key={`${event.type}-${event.timestamp}-${index}`} className="flex gap-2 border-b border-hype-border/50 py-1">
                  <span className="text-gray-600">{new Date(event.timestamp * 1000).toLocaleTimeString()}</span>
                  <span className="text-hype-blue">[{event.type}]</span>
                  <span className="truncate text-gray-300">{formatEvent(event)}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="pb-4 text-center text-xs text-gray-600">
        Hyperliquid HyperEVM Farming Bot • Simulation Mode • Not financial advice
      </div>
    </main>
  )
}
