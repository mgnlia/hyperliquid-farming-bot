interface Props {
  history: number[];
}

export function PnlChart({ history }: Props) {
  const width = 640;
  const height = 200;

  if (history.length < 2) {
    return (
      <section className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
        <h3 className="mb-2 text-sm font-semibold text-slate-200">P&amp;L Trend</h3>
        <p className="text-sm text-slate-500">Collecting data...</p>
      </section>
    );
  }

  const min = Math.min(...history);
  const max = Math.max(...history);
  const range = Math.max(1, max - min);
  const latest = history[history.length - 1] ?? 0;
  const points = history
    .map((value, index) => {
      const x = (index / (history.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">P&amp;L Trend</h3>
        <span className={`text-xs ${latest >= 0 ? "text-emerald-300" : "text-rose-300"}`}>
          {latest >= 0 ? "+" : ""}${latest.toFixed(2)}
        </span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="h-44 w-full">
        <defs>
          <linearGradient id="pnlLine" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="100%" stopColor="#a78bfa" />
          </linearGradient>
        </defs>
        <polyline fill="none" stroke="url(#pnlLine)" strokeWidth="3" points={points} />
      </svg>
    </section>
  );
}
