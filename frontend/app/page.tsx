'use client'
import { useState, useEffect, useCallback } from 'react'
import { useSSE } from '@/lib/hooks'
import { api } from '@/lib/api'
import StatCard from '@/components/StatCard'
import AirdropScore from '@/components/AirdropScore'
import PointsPanel from '@/components/PointsPanel'
import PositionsTable from '@/components/PositionsTable'
import TradeHistory from '@/components/TradeHistory'
import PnLChart from '@/components/PnLChart'
import BotControls from '@/components/BotControls'

export default function Dashboard() {
  const { data: sseData, connected } = useSSE()
  const [portfolio, setPortfolio] = useState<any>(null)
  const [botStatus, setBotStatus] = useState<any>(null)
  const [tick, setTick] = useState(0)

  const refetch = useCallback(async () => {
    try {
      const s = await api.status()
      setBotStatus(s.bot)
      setPortfolio(s.portfolio)
    } catch {}
  }, [])

  useEffect(() => { refetch() }, [refetch])

  // Sync from SSE
  useEffect(() => {
    if (sseData) {
      setBotStatus(sseData.bot)
      setPortfolio(sseData.portfolio)
    }
  }, [sseData])

  const running = botStatus?.running ?? false
  const simMode = botStatus?.simulation_mode ?? true
  const perps = botStatus?.strategies?.perps
  const defi = botStatus?.strategies?.defi_farming
  const pts = botStatus?.strategies?.point_farmer

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-[#e5e7eb]">
      {/* Header */}
      <header className="border-b border-[#1f2937] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚡</span>
            <div>
              <h1 className="text-xl font-bold">Hyperliquid Farming Bot</h1>
              <p className="text-xs text-[#6b7280]">$HYPE Season 3 Airdrop Optimizer</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs">
              <span className={connected ? 'dot-live' : 'dot-stopped'} />
              <span className="text-[#6b7280]">{connected ? 'Live' : 'Reconnecting'}</span>
            </div>
            <BotControls running={running} simMode={simMode} onAction={() => { refetch(); setTick(t => t + 1) }} />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 flex flex-col gap-6">
        {/* KPI row */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <StatCard
            label="Total Trades"
            value={portfolio?.total_trades ?? 0}
            sub="all strategies"
            color="blue"
          />
          <StatCard
            label="Volume"
            value={`$${(portfolio?.total_volume_usd ?? 0).toFixed(0)}`}
            sub="USD traded"
            color="green"
          />
          <StatCard
            label="Today's Trades"
            value={portfolio?.today_trades ?? 0}
            sub={new Date().toLocaleDateString()}
          />
          <StatCard
            label="Perps Volume"
            value={`$${(perps?.total_volume_usd ?? 0).toFixed(0)}`}
            sub={`${perps?.total_trades ?? 0} trades`}
            color="blue"
          />
          <StatCard
            label="DeFi Yield"
            value={`$${(defi?.total_yield_usd ?? 0).toFixed(4)}`}
            sub={`${defi?.active_positions ?? 0} positions`}
            color="purple"
          />
          <StatCard
            label="Points"
            value={(pts?.total_points ?? 0).toFixed(0)}
            sub={`rank ~#${(pts?.estimated_rank ?? 0).toLocaleString()}`}
            color="yellow"
          />
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Airdrop + Points */}
          <div className="flex flex-col gap-6">
            <AirdropScore />
            <PointsPanel />
          </div>

          {/* Middle: Chart + Positions */}
          <div className="flex flex-col gap-6">
            <PnLChart />
            <PositionsTable />
          </div>

          {/* Right: Strategy cards + Trade history */}
          <div className="flex flex-col gap-6">
            {/* Strategy status */}
            <div className="card flex flex-col gap-3">
              <h2 className="text-lg font-bold">🤖 Strategy Status</h2>
              {[
                { key: 'perps', label: 'Perps Trader', icon: '📈', data: perps },
                { key: 'defi', label: 'DeFi Farmer', icon: '🌾', data: defi },
                { key: 'points', label: 'Point Farmer', icon: '⭐', data: pts },
              ].map(({ key, label, icon, data }) => (
                <div key={key} className="flex items-center justify-between bg-[#1f2937] rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <span>{icon}</span>
                    <span className="text-sm font-medium">{label}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={data?.running ? 'dot-live' : 'dot-stopped'} />
                    <span className={`text-xs ${data?.running ? 'text-[#00d4a0]' : 'text-[#6b7280]'}`}>
                      {data?.running ? 'Running' : 'Idle'}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Risk summary */}
            <div className="card">
              <h2 className="text-lg font-bold mb-3">🛡 Risk Monitor</h2>
              <div className="flex flex-col gap-2 text-sm">
                {botStatus?.risk && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-[#6b7280]">Exposure</span>
                      <span>${botStatus.risk.total_exposure_usd?.toFixed(0)} / ${botStatus.risk.max_exposure_usd}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#6b7280]">Drawdown</span>
                      <span className={botStatus.risk.drawdown_pct > 7 ? 'text-[#ef4444]' : 'text-[#00d4a0]'}>
                        {botStatus.risk.drawdown_pct?.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#6b7280]">Status</span>
                      <span className={botStatus.risk.blocked ? 'text-[#ef4444]' : 'text-[#00d4a0]'}>
                        {botStatus.risk.blocked ? `BLOCKED: ${botStatus.risk.block_reason}` : 'OK'}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Full-width trade history */}
        <TradeHistory />

        <footer className="text-center text-xs text-[#6b7280] pb-4">
          Hyperliquid Farming Bot • $HYPE Season 3 •{' '}
          {simMode ? '⚠ Simulation Mode — no real funds at risk' : '🔴 Live Trading'}
        </footer>
      </main>
    </div>
  )
}
