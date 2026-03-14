"use client";

import { useEffect, useMemo, useState } from "react";

import { EventFeed } from "@/components/EventFeed";
import { PnlChart } from "@/components/PnlChart";
import { PointsPanel } from "@/components/PointsPanel";
import { PositionsTable } from "@/components/PositionsTable";
import { StatusCard } from "@/components/StatusCard";
import { TradeTable } from "@/components/TradeTable";
import {
  api,
  type BotStatus,
  type DefiPosition,
  type PerpPosition,
  type PointsResponse,
  type TradesResponse,
} from "@/lib/api";

export default function HomePage() {
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [perps, setPerps] = useState<PerpPosition[]>([]);
  const [defi, setDefi] = useState<DefiPosition[]>([]);
  const [points, setPoints] = useState<PointsResponse | null>(null);
  const [trades, setTrades] = useState<TradesResponse["trades"]>([]);
  const [events, setEvents] = useState<Array<Record<string, unknown>>>([]);
  const [pnlHistory, setPnlHistory] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      const [statusData, positionsData, pointsData, tradesData] = await Promise.all([
        api.status(),
        api.positions(),
        api.points(),
        api.trades(),
      ]);
      setStatus(statusData);
      setPerps(positionsData.perps);
      setDefi(positionsData.defi);
      setPoints(pointsData);
      setTrades(tradesData.trades);
      setPnlHistory((previous) => {
        const next = [...previous, statusData.realized_pnl + statusData.unrealized_pnl + statusData.defi_earned];
        return next.slice(-100);
      });
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
    let eventSource: EventSource | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let closed = false;

    const connect = () => {
      eventSource = new EventSource(api.streamUrl());

      eventSource.onmessage = (message) => {
        try {
          const parsed = JSON.parse(message.data) as Record<string, unknown>;
          setEvents((previous) => [...previous.slice(-99), parsed]);
        } catch {
          // ignore malformed event payloads
        }
      };

      eventSource.onerror = () => {
        eventSource?.close();
        if (!closed && reconnectTimer === null) {
          reconnectTimer = setTimeout(() => {
            reconnectTimer = null;
            connect();
          }, 3000);
        }
      };
    };

    connect();

    return () => {
      closed = true;
      eventSource?.close();
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
    };
  }, []);

  const handleStart = async () => {
    try {
      await api.start();
      await refresh();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to start agent");
    }
  };

  const handleStop = async () => {
    try {
      await api.stop();
      await refresh();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to stop agent");
    }
  };

  const totalPnl = useMemo(() => {
    if (!status) {
      return 0;
    }
    return status.realized_pnl + status.unrealized_pnl + status.defi_earned;
  }, [status]);

  return (
    <main className="mx-auto max-w-7xl space-y-6 px-4 py-8">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Hyperliquid HyperEVM Farming Bot</h1>
          <p className="text-sm text-slate-400">
            Season 3 simulator dashboard · SIMULATION_MODE {status?.simulation_mode ? "enabled" : "disabled"}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => void handleStart()}
            className="rounded-lg border border-emerald-700 bg-emerald-900/40 px-4 py-2 text-sm text-emerald-200 hover:bg-emerald-800/40"
          >
            Start Agent
          </button>
          <button
            onClick={() => void handleStop()}
            className="rounded-lg border border-rose-700 bg-rose-900/40 px-4 py-2 text-sm text-rose-200 hover:bg-rose-800/40"
          >
            Stop Agent
          </button>
        </div>
      </header>

      {error ? (
        <div className="rounded-lg border border-rose-700 bg-rose-950/50 p-3 text-sm text-rose-200">Error: {error}</div>
      ) : null}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatusCard
          title="Agent Status"
          value={loading ? "Loading..." : status?.status ?? "unknown"}
          note="running | stopped | halted"
          tone={status?.status === "running" ? "green" : status?.status === "halted" ? "red" : "blue"}
        />
        <StatusCard
          title="Portfolio Value"
          value={`$${(status?.portfolio_value ?? 0).toFixed(2)}`}
          note="Simulated equity"
          tone="blue"
        />
        <StatusCard
          title="Total P&L"
          value={`${totalPnl >= 0 ? "+" : ""}$${totalPnl.toFixed(2)}`}
          note="Realized + unrealized + yield"
          tone={totalPnl >= 0 ? "green" : "red"}
        />
        <StatusCard
          title="Airdrop Score"
          value={`${(status?.airdrop_score ?? 0).toFixed(2)} / 100`}
          note={`${(status?.total_points ?? 0).toFixed(2)} total points`}
          tone="yellow"
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <PnlChart history={pnlHistory} />
        </div>
        <PointsPanel total={points?.total_points ?? 0} score={points?.airdrop_score ?? 0} protocols={points?.breakdown ?? []} />
      </section>

      <PositionsTable perps={perps} defi={defi} />

      <section className="grid gap-4 xl:grid-cols-2">
        <TradeTable trades={trades} />
        <EventFeed events={events} />
      </section>
    </main>
  );
}
