'use client'

import { useEffect, useMemo, useState } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface StatusResponse {
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

interface PositionsResponse {
  perps: Array<{
    symbol: string
    side: string
    size: number
    entry_price: number
    current_price: number
    unrealized_pnl: number
    opened_at: number
  }>
  defi: Array<{
    protocol: string
    pool: string
    deposited: number
    apy: number
    earned: number
  }>
}

interface PointsResponse {
  breakdown: Array<{
    protocol: string
    points: number
    multiplier: number
    actions_count: number
  }>
  total_points: number
  airdrop_score: number
}

interface TradesResponse {
  trades: Array<{
    type: string
    symbol?: string
    price?: number
    entry_price?: number
    exit_price?: number
    pnl?: number
    timestamp: number
  }>
}

interface StreamEvent {
  type: string
  timestamp: number
  protocol?: string
  symbol?: string
  total_points?: number
  portfolio_value?: number
  pnl?: number
}

function cardClassName() {
  return 'rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-sm shadow-black/20'
}

export default function HomePage() {
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [positions, setPositions] = useState<PositionsResponse>({ perps: [], defi: [] })
  const [points, setPoints] = useState<PointsResponse>({ breakdown: [], total_points: 0, airdrop_score: 0 })
  const [trades, setTrades] = useState<TradesResponse['trades']>([])
  const [events, setEvents] = useState<StreamEvent[]>([])
  const [connected, setConnected] = useState(false)
  const [history, setHistory] = useState<number[]>([])

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [statusRes, positionsRes, pointsRes, tradesRes] = await Promise.all([
          fetch(`${API}/api/status`),
          fetch(`${API}/api/positions`),
          fetch(`${API}/api/points`),
          fetch(`${API}/api/trades`),
        ])

        if (!cancelled && statusRes.ok) {
          const nextStatus = (await statusRes.json()) as StatusResponse
          setStatus(nextStatus)
          setHistory((current) => [...current.slice(-23), nextStatus.portfolio_value])
        }

        if (!cancelled && positionsRes.ok) {
          setPositions((await positionsRes.json()) as PositionsResponse)
        }

        if (!cancelled && pointsRes.ok) {
          setPoints((await pointsRes.json()) as PointsResponse)
        }

        if (!cancelled && tradesRes.ok) {
          const payload = (await tradesRes.json()) as TradesResponse
          setTrades(payload.trades)
        }
      } catch {
        if (!cancelled) {
          setConnected(false)
        }
      }
    }

    void load()
    const interval = window.setInterval(() => {
      void load()
    }, 3000)

    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [])

  useEffect(() => {
    const source = new EventSource(`${API}/api/stream`)

    source.onmessage = (message) => {
      try {
        const nextEvent = JSON.parse(message.data) as StreamEvent
        setConnected(true)
        setEvents((current) => [...current.slice(-59), nextEvent])
        if (typeof nextEvent.portfolio_value === 'number') {
          setHistory((current) => [...current.slice(-23), nextEvent.portfolio_value as number])
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

  async function controlAgent(action: 'start' | 'stop') {
    await fetch(`${API}/api/agent/${action}`, { method: 'POST' })
  }

  const chartBars = useMemo(() => {
    if (history.length === 0) {
      return []
    }

    const minimum = Math.min(...history)
    const maximum = Math.max(...history)
    const range = Math.max(1, maximum - minimum)

    return history.map((value, index) => ({
      id: `${index}-${value}`,
      height: `${20 + ((value - minimum) / range) * 80}%`,
      value,
    }))
  }, [history])

  const latestTradeRows = [...trades].reverse().slice(0, 8)
  const latestEvents = [...events].reverse().slice(0, 10)
  const score = points.airdrop_score || status?.airdrop_score || 0
  const scoreWidth = `${Math.max(0, Math.min(100, score))}%`

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-4 py-8 text-slate-100">
      <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-cyan-400">HyperEVM simulator</p>
          <h1 className="mt-2 text-4xl font-semibold">Hyperliquid Farming Bot</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-400">
            Simulation-first dashboard for perps farming, HyperEVM DeFi allocation, and cross-protocol points accumulation.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${status?.simulation_mode ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300'}`}>
            {status?.simulation_mode ? 'SIMULATION MODE' : 'LIVE MODE'}
          </span>
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${connected ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}`}>
            {connected ? 'SSE CONNECTED' : 'SSE DISCONNECTED'}
          </span>
          <button className="rounded-xl bg-cyan-500 px-4 py-2 text-sm font-medium text-slate-950" onClick={() => void controlAgent('start')}>
            Start Agent
          </button>
          <button className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200" onClick={() => void controlAgent('stop')}>
            Stop Agent
          </button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <section className={cardClassName()}>
          <p className="text-sm text-slate-400">Portfolio Value</p>
          <p className="mt-2 text-3xl font-semibold">${(status?.portfolio_value ?? 0).toFixed(2)}</p>
          <p className="mt-2 text-xs text-slate-500">Cash ${(status?.cash ?? 0).toFixed(2)}</p>
        </section>

        <section className={cardClassName()}>
          <p className="text-sm text-slate-400">Perps P&amp;L</p>
          <p className="mt-2 text-3xl font-semibold text-emerald-300">${(status?.realized_pnl ?? 0).toFixed(2)}</p>
          <p className="mt-2 text-xs text-slate-500">Unrealized ${(status?.unrealized_pnl ?? 0).toFixed(2)}</p>
        </section>

        <section className={cardClassName()}>
          <p className="text-sm text-slate-400">Farmed Points</p>
          <p className="mt-2 text-3xl font-semibold">{(points.total_points ?? 0).toFixed(0)}</p>
          <p className="mt-2 text-xs text-slate-500">DeFi earned ${(status?.defi_earned ?? 0).toFixed(2)}</p>
        </section>

        <section className={cardClassName()}>
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">Airdrop Score</p>
            <p className="text-lg font-semibold text-cyan-300">{score.toFixed(1)}</p>
          </div>
          <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-800">
            <div className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-emerald-400" style={{ width: scoreWidth }} />
          </div>
          <p className="mt-2 text-xs text-slate-500">Higher score means broader protocol coverage and more point velocity.</p>
        </section>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <section className={cardClassName()}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">P&amp;L Trend</h2>
              <p className="text-sm text-slate-400">Recent portfolio samples from REST + SSE updates</p>
            </div>
            <div className="text-right text-sm text-slate-400">
              <div>Peak ${(status?.risk_metrics.peak_value ?? 0).toFixed(2)}</div>
              <div>Drawdown {((status?.risk_metrics.current_drawdown ?? 0) * 100).toFixed(2)}%</div>
            </div>
          </div>
          <div className="mt-6 flex h-48 items-end gap-2 rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
            {chartBars.length === 0 ? (
              <div className="m-auto text-sm text-slate-500">Waiting for agent samples...</div>
            ) : (
              chartBars.map((bar) => (
                <div key={bar.id} className="flex-1 rounded-t-lg bg-cyan-400/80" style={{ height: bar.height }} title={`$${bar.value.toFixed(2)}`} />
              ))
            )}
          </div>
        </section>

        <section className={cardClassName()}>
          <h2 className="text-xl font-semibold">Strategy Snapshot</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between border-b border-slate-800 pb-3">
              <dt className="text-slate-400">Agent status</dt>
              <dd className="capitalize">{status?.status ?? 'loading'}</dd>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-3">
              <dt className="text-slate-400">Open perp positions</dt>
              <dd>{positions.perps.length}</dd>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-3">
              <dt className="text-slate-400">Active DeFi allocations</dt>
              <dd>{positions.defi.length}</dd>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-3">
              <dt className="text-slate-400">Risk state</dt>
              <dd className={status?.risk_metrics.is_halted ? 'text-rose-300' : 'text-emerald-300'}>
                {status?.risk_metrics.is_halted ? 'Halted' : 'Healthy'}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-400">Tracked protocols</dt>
              <dd>Felix, Mizu, Drip, Hyperbeat</dd>
            </div>
          </dl>
        </section>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <section className={cardClassName()}>
          <h2 className="text-xl font-semibold">Positions</h2>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left text-slate-400">
                <tr>
                  <th className="pb-3">Type</th>
                  <th className="pb-3">Name</th>
                  <th className="pb-3 text-right">Value</th>
                  <th className="pb-3 text-right">Metric</th>
                </tr>
              </thead>
              <tbody>
                {positions.perps.map((position) => (
                  <tr key={`${position.symbol}-${position.opened_at}`} className="border-t border-slate-800">
                    <td className="py-3">Perp</td>
                    <td className="py-3">{position.symbol} {position.side}</td>
                    <td className="py-3 text-right">${position.current_price.toFixed(2)}</td>
                    <td className="py-3 text-right">PnL ${position.unrealized_pnl.toFixed(2)}</td>
                  </tr>
                ))}
                {positions.defi.map((position) => (
                  <tr key={`${position.protocol}-${position.pool}`} className="border-t border-slate-800">
                    <td className="py-3">DeFi</td>
                    <td className="py-3">{position.protocol} · {position.pool}</td>
                    <td className="py-3 text-right">${position.deposited.toFixed(2)}</td>
                    <td className="py-3 text-right">APY {(position.apy * 100).toFixed(1)}%</td>
                  </tr>
                ))}
                {positions.perps.length === 0 && positions.defi.length === 0 ? (
                  <tr>
                    <td className="py-6 text-slate-500" colSpan={4}>No active positions yet.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>

        <section className={cardClassName()}>
          <h2 className="text-xl font-semibold">Protocol Points</h2>
          <div className="mt-4 space-y-3">
            {points.breakdown.map((entry) => (
              <div key={entry.protocol}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span>{entry.protocol}</span>
                  <span className="text-slate-400">{entry.points.toFixed(0)} pts · {entry.actions_count} actions</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                  <div className="h-full rounded-full bg-emerald-400" style={{ width: `${Math.min(100, entry.points / 10)}%` }} />
                </div>
              </div>
            ))}
            {points.breakdown.length === 0 ? <p className="text-sm text-slate-500">Waiting for point farming events...</p> : null}
          </div>
        </section>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <section className={cardClassName()}>
          <h2 className="text-xl font-semibold">Latest Trades</h2>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left text-slate-400">
                <tr>
                  <th className="pb-3">Time</th>
                  <th className="pb-3">Type</th>
                  <th className="pb-3">Symbol</th>
                  <th className="pb-3 text-right">Price</th>
                  <th className="pb-3 text-right">PnL</th>
                </tr>
              </thead>
              <tbody>
                {latestTradeRows.map((trade) => (
                  <tr key={`${trade.type}-${trade.timestamp}-${trade.symbol ?? 'x'}`} className="border-t border-slate-800">
                    <td className="py-3">{new Date(trade.timestamp * 1000).toLocaleTimeString()}</td>
                    <td className="py-3">{trade.type}</td>
                    <td className="py-3">{trade.symbol ?? '-'}</td>
                    <td className="py-3 text-right">${Number(trade.price ?? trade.exit_price ?? trade.entry_price ?? 0).toFixed(2)}</td>
                    <td className="py-3 text-right">${Number(trade.pnl ?? 0).toFixed(2)}</td>
                  </tr>
                ))}
                {latestTradeRows.length === 0 ? (
                  <tr>
                    <td className="py-6 text-slate-500" colSpan={5}>No trades yet.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>

        <section className={cardClassName()}>
          <h2 className="text-xl font-semibold">Event Feed</h2>
          <div className="mt-4 space-y-3 text-sm">
            {latestEvents.map((event, index) => (
              <div key={`${event.type}-${event.timestamp}-${index}`} className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-cyan-300">{event.type}</span>
                  <span className="text-xs text-slate-500">{new Date(event.timestamp * 1000).toLocaleTimeString()}</span>
                </div>
                <p className="mt-1 text-slate-400">
                  {event.protocol ? `Protocol ${event.protocol}. ` : ''}
                  {event.symbol ? `Symbol ${event.symbol}. ` : ''}
                  {typeof event.portfolio_value === 'number' ? `Portfolio $${event.portfolio_value.toFixed(2)}. ` : ''}
                  {typeof event.total_points === 'number' ? `Points ${event.total_points.toFixed(0)}. ` : ''}
                  {typeof event.pnl === 'number' ? `PnL $${event.pnl.toFixed(2)}.` : ''}
                </p>
              </div>
            ))}
            {latestEvents.length === 0 ? <p className="text-sm text-slate-500">No streamed events yet.</p> : null}
          </div>
        </section>
      </div>
    </main>
  )
}
