"use client";
import type { Trade } from "@/lib/api";

interface TradeTableProps {
  trades: Trade[];
}

export function TradeTable({ trades }: TradeTableProps) {
  if (!trades.length) {
    return <p className="text-gray-500 text-sm">No trades yet.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-400 border-b border-gray-700">
            <th className="text-left py-2 pr-4">Time</th>
            <th className="text-left py-2 pr-4">Market</th>
            <th className="text-left py-2 pr-4">Side</th>
            <th className="text-right py-2 pr-4">Size</th>
            <th className="text-right py-2 pr-4">Price</th>
            <th className="text-right py-2">PnL</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t) => (
            <tr key={t.id} className="border-b border-gray-800 hover:bg-gray-800/50">
              <td className="py-1.5 pr-4 text-gray-400 text-xs">
                {new Date(t.timestamp).toLocaleTimeString()}
              </td>
              <td className="py-1.5 pr-4 font-medium">{t.market}</td>
              <td className={`py-1.5 pr-4 font-medium ${
                t.side === "long" ? "text-green-400" : t.side === "short" ? "text-red-400" : "text-gray-400"
              }`}>
                {t.side.toUpperCase()}
              </td>
              <td className="py-1.5 pr-4 text-right">${t.size.toFixed(2)}</td>
              <td className="py-1.5 pr-4 text-right">${t.price.toFixed(2)}</td>
              <td className={`py-1.5 text-right font-medium ${t.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                {t.pnl >= 0 ? "+" : ""}{t.pnl.toFixed(4)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
