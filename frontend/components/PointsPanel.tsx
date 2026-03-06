import type { PointsProtocol } from "@/lib/api";

interface Props {
  total: number;
  score: number;
  protocols: PointsProtocol[];
}

export function PointsPanel({ total, score, protocols }: Props) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <div className="mb-4 flex items-end justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">Airdrop Points</h3>
          <p className="text-2xl font-semibold text-yellow-300">{total.toFixed(2)} pts</p>
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-wider text-slate-400">Score Meter</p>
          <p className="text-lg font-semibold text-fuchsia-300">{score.toFixed(2)} / 100</p>
        </div>
      </div>

      <div className="mb-4 h-3 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-full rounded-full bg-gradient-to-r from-fuchsia-500 via-purple-400 to-cyan-400"
          style={{ width: `${Math.min(100, score)}%` }}
        />
      </div>

      <div className="space-y-2">
        {protocols.map((protocol) => {
          const width = total > 0 ? (protocol.points / total) * 100 : 0;
          return (
            <div key={protocol.protocol}>
              <div className="mb-1 flex justify-between text-xs text-slate-300">
                <span>
                  {protocol.protocol} · x{protocol.multiplier.toFixed(2)}
                </span>
                <span>{protocol.points.toFixed(2)} pts</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-500"
                  style={{ width: `${Math.min(100, width)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
