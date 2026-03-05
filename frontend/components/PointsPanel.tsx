'use client'
import { usePoints } from '@/lib/hooks'

const COLORS: Record<string, string> = {
  felix: '#8b5cf6',
  mizu: '#3b82f6',
  drip: '#00d4a0',
  hyperbeat: '#f59e0b',
  hyperliquid_native: '#ef4444',
}

export default function PointsPanel() {
  const data = usePoints()

  if (!data) return (
    <div className="card">
      <h2 className="text-lg font-bold mb-4">⭐ Protocol Points</h2>
      <div className="text-[#6b7280] text-sm">Loading...</div>
    </div>
  )

  const protocols = data.protocols || {}
  const total = data.total_points || 0

  return (
    <div className="card flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">⭐ Protocol Points</h2>
        <span className="text-[#00d4a0] font-bold">{total.toFixed(1)} pts</span>
      </div>

      <div className="flex flex-col gap-3">
        {Object.entries(protocols).map(([key, p]: [string, any]) => {
          const pct = total > 0 ? (p.points / total) * 100 : 0
          const color = COLORS[key] || '#6b7280'
          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{p.name}</span>
                  <span className="text-xs text-[#6b7280] px-1.5 py-0.5 rounded bg-[#1f2937]">{p.category}</span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold" style={{ color }}>{p.points.toFixed(2)}</span>
                  <span className="text-xs text-[#6b7280] ml-1">×{p.multiplier}</span>
                </div>
              </div>
              <div className="w-full bg-[#1f2937] rounded-full h-1.5">
                <div
                  className="h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${pct}%`, backgroundColor: color }}
                />
              </div>
            </div>
          )
        })}
      </div>

      <div className="border-t border-[#1f2937] pt-3 flex justify-between text-xs text-[#6b7280]">
        <span>Est. Rank: #{data.estimated_rank?.toLocaleString()}</span>
        <span>{Object.keys(protocols).length} protocols active</span>
      </div>
    </div>
  )
}
