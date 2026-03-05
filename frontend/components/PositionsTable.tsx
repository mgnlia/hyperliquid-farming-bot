"use client";

import type { DefiPosition, PerpPosition } from "@/lib/api";

interface Props {
  perps: PerpPosition[];
  defi: DefiPosition[];
}

export function PositionsTable({ perps, defi }: Props) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <section className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
        <h3 className="mb-3 text-sm font-semibold text-slate-200">Perps Positions</h3>
        {perps.length === 0 ? (
          <p className="text-sm text-slate-500">No open positions.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-left text-slate-400">
                  <th className="py-2 pr-3">Symbol</th>
                  <th className="py-2 pr-3">Side</th>
                  <th className="py-2 pr-3 text-right">Size</th>
                  <th className="py-2 pr-3 text-right">Entry</th>
                  <th className="py-2 text-right">PnL</th>
                </tr>
              </thead>
              <tbody>
                {perps.map((p) => (
                  <tr key={`${p.symbol}-${p.opened_at}`} className="border-b border-slate-900">
                    <td className="py-2 pr-3">{p.symbol}</td>
                    <td className={`py-2 pr-3 ${p.side === "long" ? "text-emerald-300" : "text-rose-300"}`}>
                      {p.side}
                    </td>
                    <td className="py-2 pr-3 text-right">{p.size.toFixed(4)}</td>
                    <td className="py-2 pr-3 text-right">${p.entry_price.toFixed(2)}</td>
                    <td className={`py-2 text-right ${p.unrealized_pnl >= 0 ? "text-emerald-300" : "text-rose-300"}`}>
                      {p.unrealized_pnl >= 0 ? "+" : ""}${p.unrealized_pnl.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
        <h3 className="mb-3 text-sm font-semibold text-slate-200">DeFi Farming Positions</h3>
        {defi.length === 0 ? (
          <p className="text-sm text-slate-500">No active DeFi pools.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-left text-slate-400">
                  <th className="py-2 pr-3">Protocol</th>
                  <th className="py-2 pr-3">Pool</th>
                  <th className="py-2 pr-3 text-right">Deposit</th>
                  <th className="py-2 pr-3 text-right">APY</th>
                  <th className="py-2 text-right">Earned</th>
                </tr>
              </thead>
              <tbody>
                {defi.map((p) => (
                  <tr key={`${p.protocol}-${p.pool}`} className="border-b border-slate-900">
                    <td className="py-2 pr-3">{p.protocol}</td>
                    <td className="py-2 pr-3">{p.pool}</td>
                    <td className="py-2 pr-3 text-right">${p.deposited.toFixed(2)}</td>
                    <td className="py-2 pr-3 text-right">{(p.apy * 100).toFixed(1)}%</td>
                    <td className="py-2 text-right text-emerald-300">${p.earned.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
