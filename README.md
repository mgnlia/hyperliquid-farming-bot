# Hyperliquid HyperEVM Airdrop Farming Bot

Automated airdrop farming bot for Hyperliquid's HyperEVM ecosystem — targeting $HYPE Season 3.

## Features

- **3 Strategies**: Perpetual futures trading (HIP-3), DeFi farming (KittenSwap, HypurrFi, HyperLend), Cross-protocol point farming (Felix, Mizu, Drip, Hyperbeat)
- **Risk Management**: Kelly criterion sizing, max drawdown circuit breaker, daily loss cap, position size limits
- **API Auth**: Bearer token via `BOT_API_KEY` env var (disabled when empty — dev/CI mode)
- **Real-time Dashboard**: Next.js 14 + Tailwind CSS with SSE live event streaming
- **Simulation Mode**: Runs fully simulated by default — no wallet or API keys required

## Architecture

```
backend/                   FastAPI + Python 3.11
├── config.py              Pydantic settings (env vars)
├── risk.py                Risk management (Kelly, drawdown, daily loss cap)
├── agent.py               Main async loop orchestrating strategies
├── main.py                FastAPI endpoints + SSE + Bearer auth
├── strategies/
│   ├── perps.py           Perpetual futures trading
│   ├── defi_farming.py    LP, staking, lending
│   └── point_farmer.py    Cross-protocol point accumulation
└── tests/
    └── test_bot.py        Unit + integration tests (pytest-asyncio)

frontend/                  Next.js 14 + Tailwind
└── src/app/
    ├── layout.tsx
    └── page.tsx           Dashboard: positions, points, P&L, events
```

## Quick Start

### Backend (run from repo root)
```bash
pip install uv
uv pip install --system fastapi uvicorn httpx sse-starlette pydantic pydantic-settings
uvicorn backend.main:app --reload
```

### Run Tests
```bash
uv pip install --system pytest pytest-asyncio anyio httpx
pytest backend/tests/ -v
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SIMULATION_MODE` | `true` | Run in simulation mode |
| `BOT_API_KEY` | `` | Bearer token for API auth (empty = disabled) |
| `HYPERLIQUID_PRIVATE_KEY` | `` | Private key for live trading |
| `INITIAL_PORTFOLIO_VALUE` | `10000` | Starting portfolio value |
| `MAX_POSITION_PCT` | `0.25` | Max single position size (Kelly cap) |
| `MAX_DRAWDOWN_PCT` | `0.15` | Max drawdown before circuit breaker halt |
| `DAILY_LOSS_CAP_USD` | `500` | Max daily loss in USD before halt |
| `MAX_TRADES_PER_DAY` | `50` | Max trades per day (resets at midnight) |

## API Endpoints

All endpoints except `/health` require `Authorization: Bearer <BOT_API_KEY>` when `BOT_API_KEY` is set.

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check (no auth) |
| GET | `/api/status` | Agent status and portfolio |
| GET | `/api/positions` | Open positions (perps + DeFi) |
| GET | `/api/points` | Points breakdown per protocol |
| GET | `/api/trades` | Recent trade history |
| POST | `/api/agent/start` | Start the agent |
| POST | `/api/agent/stop` | Stop the agent |
| POST | `/api/agent/resume` | Resume after halt |
| GET | `/api/stream` | SSE live event stream |

## Risk Management

- **Drawdown circuit breaker**: halts trading when portfolio drops ≥ `MAX_DRAWDOWN_PCT` from peak
- **Daily loss cap**: halts when realized losses exceed `DAILY_LOSS_CAP_USD` in a single day
- **Daily reset**: trade count and daily loss counters reset at midnight automatically
- **Position sizing**: Kelly criterion with `MAX_POSITION_PCT` hard cap

## License

MIT
