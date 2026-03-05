'use client'
import { useState } from 'react'
import { api } from '@/lib/api'

interface Props {
  running: boolean
  simMode: boolean
  onAction: () => void
}

export default function BotControls({ running, simMode, onAction }: Props) {
  const [loading, setLoading] = useState(false)

  async function handleStart() {
    setLoading(true)
    try { await api.startBot(); onAction() } catch {} finally { setLoading(false) }
  }
  async function handleStop() {
    setLoading(true)
    try { await api.stopBot(); onAction() } catch {} finally { setLoading(false) }
  }
  async function handleResetRisk() {
    setLoading(true)
    try { await api.resetRisk(); onAction() } catch {} finally { setLoading(false) }
  }

  return (
    <div className="flex items-center gap-3 flex-wrap">
      {running ? (
        <button
          onClick={handleStop}
          disabled={loading}
          className="px-4 py-2 bg-[#ef4444]/10 text-[#ef4444] border border-[#ef4444]/30 rounded-lg text-sm font-medium hover:bg-[#ef4444]/20 transition-colors disabled:opacity-50"
        >
          ⏹ Stop Bot
        </button>
      ) : (
        <button
          onClick={handleStart}
          disabled={loading}
          className="px-4 py-2 bg-[#00d4a0]/10 text-[#00d4a0] border border-[#00d4a0]/30 rounded-lg text-sm font-medium hover:bg-[#00d4a0]/20 transition-colors disabled:opacity-50"
        >
          ▶ Start Bot
        </button>
      )}
      <button
        onClick={handleResetRisk}
        disabled={loading}
        className="px-4 py-2 bg-[#f59e0b]/10 text-[#f59e0b] border border-[#f59e0b]/30 rounded-lg text-sm font-medium hover:bg-[#f59e0b]/20 transition-colors disabled:opacity-50"
      >
        🔓 Reset Risk
      </button>
      {simMode && (
        <span className="px-3 py-1.5 bg-[#f59e0b]/10 text-[#f59e0b] border border-[#f59e0b]/30 rounded-full text-xs font-medium">
          ⚠ SIMULATION MODE
        </span>
      )}
    </div>
  )
}
