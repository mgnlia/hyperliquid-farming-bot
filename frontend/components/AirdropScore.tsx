'use client'
import { useAirdrop } from '@/lib/hooks'

export default function AirdropScore() {
  const data = useAirdrop()

  if (!data) return (
    <div className="card">
      <h2 className="text-lg font-bold mb-4">🪂 $HYPE Airdrop Score</h2>
      <div className="text-[#6b7280] text-sm">Loading...</div>
    </div>
  )

  const score = data.airdrop_score ?? 0
  const scoreColor = score >= 80 ? '#00d4a0' : score >= 50 ? '#f59e0b' : '#ef4444'
  const checks = data.checks || {}

  const checkLabels: Record<string, string> = {
    trading_volume_ok: '$1,000+ trading volume',
    defi_active: '2+ active DeFi positions',
    points_farming: '100+ protocol points',
    multi_protocol: '3+ protocols active',
    consistent_activity: '50+ total trades',
  }

  return (
    <div className="card flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">🪂 $HYPE Airdrop Score</h2>
        <span className="text-xs badge-purple px-2 py-1 rounded-full">Season 3</span>
      </div>

      {/* Score meter */}
      <div className="flex items-center gap-4">
        <div className="relative w-20 h-20 flex-shrink-0">
          <svg viewBox="0 0 36 36" className="w-20 h-20 -rotate-90">
            <circle cx="18" cy="18" r="15.9" fill="none" stroke="#1f2937" strokeWidth="3" />
            <circle
              cx="18" cy="18" r="15.9" fill="none"
              stroke={scoreColor} strokeWidth="3"
              strokeDasharray={`${score} 100`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xl font-bold" style={{ color: scoreColor }}>{score}</span>
          </div>
        </div>
        <div>
          <div className="text-sm font-medium text-[#e5e7eb]">
            {score >= 80 ? '🟢 Snapshot Ready' : score >= 50 ? '🟡 In Progress' : '🔴 Needs Work'}
          </div>
          <div className="text-xs text-[#6b7280] mt-1">
            {data.total_points?.toFixed(0)} pts • Rank ~#{data.estimated_rank?.toLocaleString()}
          </div>
          <div className="text-xs text-[#6b7280]">
            {data.total_trades} trades • ${data.total_volume_usd?.toFixed(0)} vol
          </div>
        </div>
      </div>

      {/* Checklist */}
      <div className="flex flex-col gap-2">
        {Object.entries(checkLabels).map(([key, label]) => (
          <div key={key} className="flex items-center gap-2">
            <span className={checks[key] ? 'text-[#00d4a0]' : 'text-[#6b7280]'}>
              {checks[key] ? '✓' : '○'}
            </span>
            <span className={`text-sm ${checks[key] ? 'text-[#e5e7eb]' : 'text-[#6b7280]'}`}>{label}</span>
          </div>
        ))}
      </div>

      {data.simulation_mode && (
        <div className="text-xs text-[#f59e0b] border-t border-[#1f2937] pt-3">
          ⚠ Simulation mode — no real on-chain activity
        </div>
      )}
    </div>
  )
}
