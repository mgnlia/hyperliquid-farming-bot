"use client";
import type { ProtocolPoints } from "@/lib/api";

interface PointsPanelProps {
  protocols: ProtocolPoints[];
  grandTotal: number;
}

export function PointsPanel({ protocols, grandTotal }: PointsPanelProps) {
  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <span className="text-gray-400 text-sm">Grand Total</span>
        <span className="text-yellow-400 font-bold text-lg">{grandTotal.toLocaleString()} pts</span>
      </div>
      <div className="space-y-2">
        {protocols.map((p) => {
          const pct = grandTotal > 0 ? (p.total_points / grandTotal) * 100 : 0;
          return (
            <div key={p.protocol}>
              <div className="flex justify-between text-sm mb-0.5">
                <span className="text-gray-300">{p.protocol}</span>
                <span className="text-yellow-300">{p.total_points.toFixed(1)} pts</span>
              </div>
              <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-yellow-500 to-orange-400 rounded-full"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
