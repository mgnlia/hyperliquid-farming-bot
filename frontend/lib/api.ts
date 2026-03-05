const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface BotStatus {
  status: string;
  simulation_mode: boolean;
  started_at: string;
  tick_count: number;
  last_tick: string;
  total_pnl: number;
  total_points: number;
}

export interface PerpPosition {
  market: string;
  side: string;
  size_usdc: number;
  entry_price: number;
  current_price: number;
  pnl: number;
}

export interface FarmPosition {
  protocol: string;
  type: string;
  amount: number;
  apy_est: number;
  points_per_day: number;
  cumulative_points: number;
  opened_at: string;
}

export interface Portfolio {
  total_pnl: number;
  total_tvl: number;
  open_perp_positions: number;
  perp_positions: PerpPosition[];
  farm_positions: FarmPosition[];
}

export interface Trade {
  id: number;
  timestamp: string;
  strategy: string;
  market: string;
  side: string;
  size: number;
  price: number;
  pnl: number;
}

export interface ProtocolPoints {
  protocol: string;
  total_points: number;
  days_active: number;
  recent_events: Array<{ reason: string; amount: number; cumulative: number; timestamp: string }>;
}

export interface PointsSummary {
  grand_total: number;
  by_protocol: ProtocolPoints[];
  db_summary: Array<{ protocol: string; total_points: number; events: number }>;
}

export interface FullStatus {
  bot: BotStatus;
  perps: {
    strategy: string;
    open_positions: number;
    trades_today: number;
    total_pnl: number;
    positions: PerpPosition[];
  };
  farming: {
    strategy: string;
    positions: FarmPosition[];
    total_tvl: number;
    total_points: number;
  };
  points: ProtocolPoints[];
}

// ── API client ────────────────────────────────────────────────────────────────

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "POST", cache: "no-store" });
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => get<{ status: string; bot: string }>("/health"),
  status: () => get<FullStatus>("/api/status"),
  portfolio: () => get<Portfolio>("/api/portfolio"),
  trades: (limit = 50) => get<{ trades: Trade[]; count: number }>(`/api/trades?limit=${limit}`),
  points: () => get<PointsSummary>("/api/points"),
  strategies: () => get<unknown>("/api/strategies"),
  botStart: () => post<{ status: string }>("/api/bot/start"),
  botStop: () => post<{ status: string }>("/api/bot/stop"),
};
