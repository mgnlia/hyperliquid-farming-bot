"use client";

import { useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type BotStatus = {
  status: string;
  simulation_mode: boolean;
  portfolio_value: number;
  cash: number;
  realized_pnl: number;
  unrealized_pnl: number;
  defi_earned: number;
  total_points: number;
  airdrop_score: number;
  started_at: number | null;
  risk_metrics?: {
    is_halted?: boolean;
    current_drawdown?: number;
    max_drawdown_pct?: number;
    max_position_pct?: number;
  };
};

type PerpPosition = {
  symbol: string;
  side: "long" | "short";
  size: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  opened_at: number;
};

type DefiPosition = {
  protocol: string;
  pool: string;
  deposited: number;
  apy: number;
  earned: number;
  started_at: number;
};

type PointsProtocol = {
  protocol: string;
  points: number;
  multiplier: number;
  actions_count: number;
  last_action: number;
};

type Trade = {
  type: string;
  symbol?: string;
  side?: string;
  pnl?: number;
  timestamp: number;
};

type PositionsResponse = {
  perps: PerpPosition[];
  defi: DefiPosition[];
};

type PointsResponse = {
  breakdown: PointsProtocol[];
  total_points: number;
  airdrop_score: number;
};

type TradesResponse = {
  trades: Trade[];
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed: ${path} (${response.status})`);
  }
  return (await response.json()) as T;
}

async function postJson(path: string): Promise<void> {
  const response = await fetch(`${API_URL}${path}`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Request failed: ${path} (${response.status})`);
  }
}

function StatCard({ title, value, subtitle }: { title: string; value: string; subtitle: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{title}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-100">{value}</p>
      <p className="mt-2 text-sm text-slate-400">{subtitle}</p>
    </div>
  );
}

export default function HomePage() {
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [positions, setPositions] = useState<PositionsResponse>({ perps: [], defi: [] });
  const [points, setPoints] = useState<PointsResponse>({ breakdown: [], total_points: 0, airdrop_score: 0 });
  const [trades, setTrades] = useState<Trade[]>([]);
  const [events, setEvents] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      const [statusData, positionsData, pointsData, tradesData] = await Promise.all([
        getJson<BotStatus>("/api/status"),
        getJson<PositionsResponse>("/api/positions"),
        getJson<PointsResponse>("/api/points"),
        getJson<TradesResponse>("/api/trades"),
      ]);
      setStatus(statusData);
      setPositions(positionsData);
      setPoints(pointsData);
      setTrades(tradesData.trades);
      setError(null);
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
    const interval = setInterval(() => {
      void refresh();
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let source: EventSource | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let disposed = false;

    const connect = () => {
      source = new EventSource(`${API_URL}/api/stream`);
      source.onmessage = (message) => {
        setEvents((current) => [message.data, ...current].slice(0, 20));
      };
      source.onerror = () => {
        source?.close();
        if (!disposed && retryTimer === null) {
          retryTimer = setTimeout(() => {
            retryTimer = null;
            connect();
          }, 3000);
        }
      };
    };

    connect();

    return () => {
      disposed = true;
      source?.close();
      if (retryTimer) {
        clearTimeout(retryTimer);
      }
    };
  }, []);

  const totalPnl = useMemo(() => {
    if (!status) {
      return 0;
    }
    return status.realized_pnl + status.unrealized_pnl + status.defi_earned;
  }, [status]);

  const onStart = async () => {
    try {
      await postJson("/api/agent/start");
      await refresh();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Unable to start agent");
    }
  };

  const onStop = async () => {
    try {
      await postJson("/api/agent/stop");
      await refresh();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Unable to stop agent");
    }
  };

  return (
    <main className="mx-auto min-h-screen max-w-7xl bg-slate-950 px-4 py-8 text-slate-100">
      <div className="space-y-6">
        <header className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-2xl shadow-slate-950/40 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-cyan-400">Hyperliquid HyperEVM</p>
            <h1 className="mt-2 text-3xl font-bold">Season 3 Farming Bot Dashboard</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              Simulation-first dashboard for perps activity, HyperEVM DeFi routing, protocol point farming, and airdrop score tracking.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              className="rounded-lg border border-emerald-700 bg-emerald-900/40 px-4 py-2 text-sm font-medium text-emerald-200 transition hover:bg-emerald-800/50"
              onClick={() => void onStart()}
            >
              Start agent
            </button>
            <button
              className="rounded-lg border border-rose-700 bg-rose-900/40 px-4 py-2 text-sm font-medium text-rose-200 transition hover:bg-rose-800/50"
              onClick={() => void onStop()}
            >
              Stop agent
            </button>
          </div>
        </header>

        {error ? <div className="rounded-xl border border-rose-700 bg-rose-950/40 p-4 text-sm text-rose-200">{error}</div> : null}

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            title="Agent"
            value={loading ? "Loading" : status?.status ?? "unknown"}
            subtitle={`Simulation mode ${status?.simulation_mode ? "enabled" : "defaulted"}`}
          />
          <StatCard
            title="Portfolio"
            value={`$${(status?.portfolio_value ?? 0).toFixed(2)}`}
            subtitle={`Cash $${(status?.cash ?? 0).toFixed(2)}`}
          />
          <StatCard
            title="Total P&L"
            value={`${totalPnl >= 0 ? "+" : ""}$${totalPnl.toFixed(2)}`}
            subtitle={`Realized $${(status?.realized_pnl ?? 0).toFixed(2)} · Unrealized $${(status?.unrealized_pnl ?? 0).toFixed(2)}`}
          />
          <StatCard
            title="Airdrop score"
            value={`${points.airdrop_score.toFixed(2)} / 100`}
            subtitle={`${points.total_points.toFixed(2)} total points farmed`}
          />
        </section>

        <section className="grid gap-4 xl:grid-cols-3">
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 xl:col-span-2">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Point protocols</h2>
              <span className="text-sm text-slate-400">Cross-protocol accumulation</span>
            </div>
            <div className="space-y-3">
              {points.breakdown.length === 0 ? (
                <p className="text-sm text-slate-500">No point data yet.</p>
              ) : (
                points.breakdown.map((protocol) => {
                  const width = points.total_points > 0 ? (protocol.points / points.total_points) * 100 : 0;
                  return (
                    <div key={protocol.protocol}>
                      <div className="mb-1 flex items-center justify-between text-sm">
                        <span className="text-slate-300">{protocol.protocol}</span>
                        <span className="text-slate-400">
                          {protocol.points.toFixed(2)} pts · x{protocol.multiplier.toFixed(2)}
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-slate-800">
                        <div
                          className="h-2 rounded-full bg-gradient-to-r from-cyan-500 via-blue-500 to-fuchsia-500"
                          style={{ width: `${Math.min(width, 100)}%` }}
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
            <h2 className="text-lg font-semibold">Risk overview</h2>
            <dl className="mt-4 space-y-3 text-sm text-slate-300">
              <div className="flex justify-between gap-3">
                <dt className="text-slate-500">Drawdown</dt>
                <dd>{Number(status?.risk_metrics?.current_drawdown ?? 0).toFixed(2)}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-slate-500">Max drawdown %</dt>
                <dd>{Number(status?.risk_metrics?.max_drawdown_pct ?? 0).toFixed(2)}%</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-slate-500">Max position %</dt>
                <dd>{Number(status?.risk_metrics?.max_position_pct ?? 0).toFixed(2)}%</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-slate-500">Started</dt>
                <dd>
                  {status?.started_at ? new Date(status.started_at * 1000).toLocaleString() : "Not started"}
                </dd>
              </div>
            </dl>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-2">
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
            <h2 className="mb-4 text-lg font-semibold">Perps positions</h2>
            {positions.perps.length === 0 ? (
              <p className="text-sm text-slate-500">No open perps positions.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-500">
                      <th className="py-2 pr-3">Symbol</th>
                      <th className="py-2 pr-3">Side</th>
                      <th className="py-2 pr-3 text-right">Size</th>
                      <th className="py-2 pr-3 text-right">Entry</th>
                      <th className="py-2 text-right">PnL</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.perps.map((position) => (
                      <tr key={`${position.symbol}-${position.opened_at}`} className="border-b border-slate-900">
                        <td className="py-2 pr-3">{position.symbol}</td>
                        <td className={`py-2 pr-3 ${position.side === "long" ? "text-emerald-300" : "text-rose-300"}`}>
                          {position.side}
                        </td>
                        <td className="py-2 pr-3 text-right">{position.size.toFixed(4)}</td>
                        <td className="py-2 pr-3 text-right">${position.entry_price.toFixed(2)}</td>
                        <td className={`py-2 text-right ${position.unrealized_pnl >= 0 ? "text-emerald-300" : "text-rose-300"}`}>
                          {position.unrealized_pnl >= 0 ? "+" : ""}${position.unrealized_pnl.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
            <h2 className="mb-4 text-lg font-semibold">DeFi farming allocations</h2>
            {positions.defi.length === 0 ? (
              <p className="text-sm text-slate-500">No active DeFi allocations.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-500">
                      <th className="py-2 pr-3">Protocol</th>
                      <th className="py-2 pr-3">Pool</th>
                      <th className="py-2 pr-3 text-right">Deposit</th>
                      <th className="py-2 pr-3 text-right">APY</th>
                      <th className="py-2 text-right">Earned</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.defi.map((position) => (
                      <tr key={`${position.protocol}-${position.pool}`} className="border-b border-slate-900">
                        <td className="py-2 pr-3">{position.protocol}</td>
                        <td className="py-2 pr-3">{position.pool}</td>
                        <td className="py-2 pr-3 text-right">${position.deposited.toFixed(2)}</td>
                        <td className="py-2 pr-3 text-right">{(position.apy * 100).toFixed(2)}%</td>
                        <td className="py-2 text-right text-emerald-300">${position.earned.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-2">
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
            <h2 className="mb-4 text-lg font-semibold">Trade log</h2>
            {trades.length === 0 ? (
              <p className="text-sm text-slate-500">No trades recorded yet.</p>
            ) : (
              <div className="max-h-80 overflow-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-500">
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
                        <tr key={`${trade.type}-${trade.timestamp}-${index}`} className="border-b border-slate-900">
                          <td className="py-2 pr-3 text-xs text-slate-400">{new Date(trade.timestamp * 1000).toLocaleTimeString()}</td>
                          <td className="py-2 pr-3">{trade.type}</td>
                          <td className="py-2 pr-3">{trade.symbol ?? "—"}</td>
                          <td className="py-2 pr-3">{trade.side ?? "—"}</td>
                          <td className={`py-2 text-right ${Number(trade.pnl ?? 0) >= 0 ? "text-emerald-300" : "text-rose-300"}`}>
                            {trade.pnl === undefined ? "—" : `${Number(trade.pnl) >= 0 ? "+" : ""}$${Number(trade.pnl).toFixed(2)}`}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
            <h2 className="mb-4 text-lg font-semibold">Live SSE feed</h2>
            {events.length === 0 ? (
              <p className="text-sm text-slate-500">Waiting for agent events.</p>
            ) : (
              <div className="max-h-80 space-y-2 overflow-auto">
                {events.map((event, index) => (
                  <pre
                    key={`${event.slice(0, 24)}-${index}`}
                    className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900/60 p-3 text-xs text-slate-300"
                  >
                    {event}
                  </pre>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
