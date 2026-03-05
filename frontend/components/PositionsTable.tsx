'use client'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

export default function PositionsTable() {
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    api.positions().then(setData).catch(() => {})
    const t = setInterval(() => api.positions().then(setData).catch(() => {}), 15000)
    return () => clearInterval(t)
  }, [])

  if (!data) return (
    <div className="card">
      <h2 className="text-lg font-bold mb-4">📊 Positions</h2>
      <div className="text-[#6b7280] text-sm">Loading...</div>
    </div>
  )

  const risk = data.risk || {}
  const positions = risk.positions || {}
  const defi = data.defi_positions || {}
  const drawdownColor = (risk.drawdown_pct || 0) > 7 ? '#ef4444' : (risk.drawdown_pct || 0) > 4 ? '#f59e0b' : '#00d4a0'

  return (
    <div className="card flex flex-col gap-4">
      <h2 className="text-lg font-bold">📊 Positions & Risk</h2>

      {/* Risk summary */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-[#1f2937] rounded-lg p-3 text-center">
          <div className="text-xs text-[#6b7280] mb-1">Exposure</div>
          <div className="text-sm font-bold text-[#3b82f6]">${risk.total_exposure_usd?.toFixed(0)}</div>
          <div className="text-xs text-[#6b7280]">/ ${risk.max_exposure_usd}</div>
        </div>
        <div className="bg-[#1f2937] rounded-lg p-3 text-center">
          <div className="text-xs text-[#6b7280] mb-1">Drawdown</div>
          <div className="text-sm font-bold" style={{ color: drawdownColor }}>{risk.drawdown_pct?.toFixed(1)}%</div>
          <div className="text-xs text-[#6b7280]">max 10%</div>
        </div>
        <div className="bg-[#1f2937] rounded-lg p-3 text-center">
          <div className="text-xs text-[#6b7280] mb-1">Status</div>
          <div className={`text-sm font-bold ${risk.blocked ? 'text-[#ef4444]' : 'text-[#00d4a0]'}`}>
            {risk.blocked ? 'BLOCKED' : 'OK'}
          </div>
          <div className="text-xs text-[#6b7280]">{risk.simulation_mode ? 'Sim' : 'Live'}</div>
        </div>
      </div>

      {/* Active perps positions */}
      {Object.keys(positions).length > 0 && (
        <div>
          <div className="text-xs text-[#6b7280] uppercase mb-2">Perps Positions</div>
          <div className="flex flex-col gap-1">
            {Object.entries(positions).map(([asset, usd]: [string, any]) => (
              <div key={asset} className="flex justify-between text-sm">
                <span className="font-medium">{asset}</span>
                <span className="text-[#3b82f6]">${usd.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* DeFi positions */}
      {Object.keys(defi).length > 0 && (
        <div>
          <div className="text-xs text-[#6b7280] uppercase mb-2">DeFi Positions</div>
          <div className="flex flex-col gap-2">
            {Object.entries(defi).map(([protocol, pos]: [string, any]) => (
              <div key={protocol} className="flex justify-between items-center text-sm">
                <div>
                  <span className="font-medium capitalize">{protocol}</span>
                  <span className="text-xs text-[#6b7280] ml-2">{pos.asset}</span>
                </div>
                <div className="text-right">
                  <span className="text-[#00d4a0]">${pos.size_usd?.toFixed(0)}</span>
                  <span className="text-xs text-[#6b7280] ml-1">{pos.apy_pct?.toFixed(0)}% APY</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {Object.keys(positions).length === 0 && Object.keys(defi).length === 0 && (
        <div className="text-[#6b7280] text-sm text-center py-4">No open positions yet</div>
      )}
    </div>
  )
}
