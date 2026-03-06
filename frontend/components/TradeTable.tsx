import type { Trade } from "@/lib/api";

interface Props {
  trades: Trade[];
}

export function TradeTable({ trades }: Props) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-200">Trade Log</h3>
      {trades.length === 0 ? (
        <p className="text-sm text-slate-500">No trades recorded yet.</p>
      ) : (
        <div className="max-h-72 overflow-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left text-slate-400">
                <th className="py-2 pr-3">Time</th>
                <th className="py-2 pr-3">Type</th>
                <th className="py-2 pr-3">Symbol</th>
                <th className="py-2 pr-3">Side</th>
                <th className="py-2 text-right">PnL</th>
              </tr>
            </thead>
            <tbody>
              {trades
                .slice()
                .reverse()
                .map((trade, index) => (
                  <tr key={`${trade.symbol ?? "trade"}-${trade.timestamp}-${index}`} className="border-b border-slate-900">
                    <td className="py-2 pr-3 text-xs text-slate-500">{new Date(trade.timestamp * 1000).toLocaleTimeString()}</td>
                    <td className="py-2 pr-3">{trade.type}</td>
                    <td className="py-2 pr-3">{trade.symbol ?? "—"}</td>
                    <td className="py-2 pr-3">{trade.side ?? "—"}</td>
                    <td className={`py-2 text-right ${Number(trade.pnl ?? 0) >= 0 ? "text-emerald-300" : "text-rose-300"}`}>
                      {trade.pnl !== undefined ? `${Number(trade.pnl) >= 0 ? "+" : ""}$${Number(trade.pnl).toFixed(2)}` : "—"}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
