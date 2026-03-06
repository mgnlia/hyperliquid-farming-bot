const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface BotStatus {
  status: string;
  simulation_mode: boolean;
  portfolio_value: number;
  cash: number;
  realized_pnl: number;
  unrealized_pnl: number;
  defi_earned: number;
  total_points: number;
  airdrop_score: number;
  risk_metrics: {
    peak_value: number;
    current_drawdown: number;
    max_drawdown_pct: number;
    max_position_pct: number;
    kelly_fraction: number;
    is_halted: boolean;
  };
  started_at: number | null;
}

export interface PerpPosition {
  symbol: string;
  side: "long" | "short";
  size: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  opened_at: number;
}

export interface DefiPosition {
  protocol: string;
  pool: string;
  deposited: number;
  apy: number;
  earned: number;
  started_at: number;
}

export interface PointsProtocol {
  protocol: string;
  points: number;
  multiplier: number;
  actions_count: number;
  last_action: number;
}

export interface PointsResponse {
  breakdown: PointsProtocol[];
  total_points: number;
  airdrop_score: number;
}

export interface TradesResponse {
  trades: Array<{
    type: string;
    symbol?: string;
    side?: string;
    size?: number;
    price?: number;
    entry_price?: number;
    exit_price?: number;
    pnl?: number;
    timestamp: number;
    created_at?: string;
    usd_value?: number;
  }>;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`${path}: ${res.status}`);
  }
  return (await res.json()) as T;
}

async function post<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`${path}: ${res.status}`);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => get<{ status: string; service: string }>("/health"),
  status: () => get<BotStatus>("/api/status"),
  positions: () => get<{ perps: PerpPosition[]; defi: DefiPosition[] }>("/api/positions"),
  points: () => get<PointsResponse>("/api/points"),
  airdrop: () => get<PointsResponse>("/api/points"),
  trades: (..._args: unknown[]) => get<TradesResponse>("/api/trades"),
  start: (..._args: unknown[]) => post<{ status: string }>("/api/agent/start"),
  stop: (..._args: unknown[]) => post<{ status: string }>("/api/agent/stop"),
  startBot: (..._args: unknown[]) => post<{ status: string }>("/api/agent/start"),
  stopBot: (..._args: unknown[]) => post<{ status: string }>("/api/agent/stop"),
  streamUrl: (..._args: unknown[]) => `${BASE}/api/stream`,
  resetRisk: (..._args: unknown[]) => post<{ status: string }>("/api/risk/reset"),
};

export function getSSEUrl(..._args: unknown[]): string {
  return `${BASE}/api/stream`;
}

export async function fetchStatus(): Promise<BotStatus> {
  return api.status();
}

export async function fetchPositions(): Promise<{ perps: PerpPosition[]; defi: DefiPosition[] }> {
  return api.positions();
}

export async function fetchPoints(): Promise<PointsResponse> {
  return api.points();
}

export async function fetchFarmEvents(): Promise<TradesResponse> {
  return api.trades();
}
