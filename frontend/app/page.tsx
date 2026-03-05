"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { PointsPanel } from "@/components/PointsPanel";
import { StatusCard } from "@/components/StatusCard";
import { TradeTable } from "@/components/TradeTable";
import { api, type FullStatus, type PointsSummary, type Trade } from "@/lib/api";

interface PnlPoint {
  t: string;
  pnl: number;
}

export default function DashboardPage() {
  const [status, setStatus] = useState<FullStatus | null>(null);
  const [points, setPoints] = useState<PointsSummary | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [pnlHistory, setPnlHistory] = useState<PnlPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [botAction, setBotAction] = useState<"idle" | "loading">("idle");

  const refresh = useCallback(async () => {
    try {
      const [s, p, t] = await Promise.all([api.status(), api.points(), api.trades(30)]);
      setStatus(s);
      setPoints(p);
      setTrades(t.trades);
      setPnlHistory((prev) => {
        const next = [
          ...prev,
          { t: new Date().toLocaleTimeString(), pnl: s.bot.total_pnl },
        ].slice(-30);
        return next;
      });
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 8000);
    return () => clearInterval(id);
  }, [refresh]);

  const handleBotToggle = async () => {
    if (!status) return;
    setBotAction("loading");
    try {
      if (status.bot.status === "running") {
        await api.botStop();
      } else {
        await api.botStart();
      }
      await refresh();
    } finally {
      setBotAction("idle");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-blue-400 animate-pulse text-xl">Loading Hyperliquid Farming Bot…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center flex-col gap-4">
        <div className="text-red-400 text-xl">⚠ API Error</div>
        <div className="text-gray-400 text-sm max-w-md text-center">{error}</div>
        <button onClick={refresh} className="px-4 py-2 bg-blue-600 rounded-lg text-white hover:bg-blue-500">
          Retry
        </button>
      </div>
    );
  }

  const bot = status?.bot;
  const isRunning = bot?.status === "running";

  return (
    <div className="min-h-screen bg-[#0a0f1e] text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">⚡</span>
          <div>
            <h1 className="text-xl font-bold text-white">Hyperliquid Farming Bot</h1>
            <p className="text-xs text-gray-400">$HYPE Season 3 Airdrop Farmer</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 text-sm ${isRunning ? "text-green-400" : "text-gray-400"}`}>
            <span className={`w-2 h-2 rounded-full ${isRunning ? "bg-green-400 animate-pulse" : "bg-gray-500"}`} />
            {isRunning ? "LIVE" : "STOPPED"}
            {bot?.simulation_mode && <span className="text-xs text-yellow-500 ml-1">[SIM]</span>}
          </div>
          <button
            onClick={handleBotToggle}
            disabled={botAction === "loading"}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              isRunning
                ? "bg-red-600/20 text-red-400 border border-red-600/40 hover:bg-red-600/30"
                : "bg-green-600/20 text-green-400 border border-green-600/40 hover:bg-green-600/30"
            } disabled:opacity-50`}
          >
            {botAction === "loading" ? "…" : isRunning ? "Stop Bot" : "Start Bot"}
          </button>
        </div>
      </header>

      <main className="px-6 py-6 space-y-6 max-w-7xl mx-auto">
        {/* KPI row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatusCard
            title="Total P&L"
            value={`$${bot?.total_pnl.toFixed(4) ?? "0.0000"}`}
            subtitle="Perps trading"
            color={bot && bot.total_pnl >= 0 ? "green" : "red"}
          />
          <StatusCard
            title="Total Points"
            value={(bot?.total_points ?? 0).toLocaleString()}
            subtitle="Across all protocols"
            color="yellow"
          />
          <StatusCard
            title="Open Positions"
            value={status?.perps.open_positions ?? 0}
            subtitle="Active perp trades"
            color="blue"
          />
          <StatusCard
            title="Total TVL"
            value={`$${(status?.farming.total_tvl ?? 0).toFixed(2)}`}
            subtitle="DeFi farming"
            color="purple"
          />
        </div>

        {/* P&L chart + Points panel */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-gray-900 rounded-xl p-5 border border-gray-800">
            <h2 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-wide">P&L Over Time</h2>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={pnlHistory}>
                <defs>
                  <linearGradient id="pnlGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="t" tick={{ fontSize: 10, fill: "#64748b" }} />
                <YAxis tick={{ fontSize: 10, fill: "#64748b" }} />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                  labelStyle={{ color: "#94a3b8" }}
                />
                <Area type="monotone" dataKey="pnl" stroke="#38bdf8" fill="url(#pnlGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <h2 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-wide">Points Breakdown</h2>
            {points ? (
              <PointsPanel protocols={points.by_protocol} grandTotal={points.grand_total} />
            ) : (
              <p className="text-gray-500 text-sm">Loading…</p>
            )}
          </div>
        </div>

        {/* Farm positions */}
        <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
          <h2 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-wide">DeFi Farm Positions</h2>
          {status?.farming.positions.length ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {status.farming.positions.map((p) => (
                <div key={p.protocol} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-semibold text-white">{p.protocol}</span>
                    <span className="text-xs bg-blue-900/50 text-blue-300 px-2 py-0.5 rounded-full">{p.type}</span>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Amount</span>
                      <span>${p.amount.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">APY</span>
                      <span className="text-green-400">{(p.apy_est * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Points/day</span>
                      <span className="text-yellow-400">{p.points_per_day}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Earned</span>
                      <span className="text-yellow-300 font-medium">{p.cumulative_points.toFixed(2)} pts</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">Bot not started or no positions yet.</p>
          )}
        </div>

        {/* Recent trades */}
        <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
          <h2 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-wide">Recent Trades</h2>
          <TradeTable trades={trades} />
        </div>

        {/* Bot stats footer */}
        <div className="bg-gray-900/50 rounded-xl p-4 border border-gray-800 text-xs text-gray-500 flex flex-wrap gap-6">
          <span>Ticks: <span className="text-gray-300">{bot?.tick_count ?? 0}</span></span>
          <span>Last tick: <span className="text-gray-300">{bot?.last_tick ? new Date(bot.last_tick).toLocaleTimeString() : "—"}</span></span>
          <span>Started: <span className="text-gray-300">{bot?.started_at ? new Date(bot.started_at).toLocaleString() : "—"}</span></span>
          <span>Trades today: <span className="text-gray-300">{status?.perps.trades_today ?? 0}</span></span>
        </div>
      </main>
    </div>
  );
}
