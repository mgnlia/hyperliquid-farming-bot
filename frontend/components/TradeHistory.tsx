'use client'
import { useTrades } from '@/lib/hooks'

const strategyColors: Record<string, string> = {
  perps: 'badge-blue',
  defi_farming: 'badge-purple',
  point_farmer: 'badge-green',
}

export default function TradeHistory() {
  const { trades, loading } = useTrades(30)

  return (
    <div className="card flex flex-col gap-4">
      <h2 className="text-lg font-bold">📋 Trade History</h2>

      {loading && <div className="text-[#6b7280] text-sm">Loading...</div>}

      {!loading && trades.length === 0 && (
        <div className="text-[#6b7280] text-sm text-center py-6">No trades yet — bot is warming up</div>
      )}

      {!loading && trades.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[#6b7280] text-xs uppercase">
                <th className="text-left pb-2">Strategy</th>
                <th className="text-left pb-2">Asset</th>
                <th className="text-left pb-2">Side</th>
                <th className="text-right pb-2">Size</th>
                <th className="text-right pb-2">Price</th>
                <th className="text-right pb-2">Value</th>
                <th className="text-right pb-2">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1f2937]">
              {trades.map((t: any) => (
                <tr key={t.id} className="hover:bg-[#1f2937]/50 transition-colors">
                  <td className="py-2">
                    <span className={`text-xs px-1.5 py-0.5 rounded ${strategyColors[t.strategy] || 'badge-yellow'}`}>
                      {t.strategy}
                    </span>
                  </td>
                  <td className="py-2 font-medium">{t.coin}</td>
                  <td className={`py-2 font-medium ${t.side === 'BUY' || t.side === 'DEPOSIT' ? 'stat-up' : 'stat-down'}`}>
                    {t.side}
                  </td>
                  <td className="py-2 text-right text-[#6b7280]">{Number(t.size).toFixed(4)}</td>
                  <td className="py-2 text-right">${Number(t.price).toFixed(2)}</td>
                  <td className="py-2 text-right text-[#3b82f6]">${Number(t.usd_value).toFixed(2)}</td>
                  <td className="py-2 text-right text-[#6b7280] text-xs">
                    {new Date(t.created_at).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
