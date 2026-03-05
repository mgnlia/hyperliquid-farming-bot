# Hyperliquid HyperEVM Airdrop Farming Bot

Automated airdrop farming bot for Hyperliquid's HyperEVM ecosystem — targeting $HYPE Season 3.

## Features

- **3 Strategies**: Perpetual futures trading (HIP-3), DeFi farming (KittenSwap, HypurrFi, HyperLend), Cross-protocol point farming (Felix, Mizu, Drip, Hyperbeat)
- **Risk Management**: Kelly criterion sizing, max drawdown limits, position size caps
- **Real-time Dashboard**: Next.js 14 + Tailwind CSS with SSE live event streaming
- **Simulation Mode**: Runs fully simulated by default — no wallet or API keys required

## Architecture

```
backend/           FastAPI + Python 3.11
├── config.py      Pydantic settings (env vars)
├── risk.py        Risk management (Kelly sizing, drawdown)
├── agent.py       Main async loop orchestrating strategies
├── main.py        FastAPI endpoints + SSE
└── strategies/
    ├── perps.py           Perpetual futures trading
    ├── defi_farming.py    LP, staking, lending
    └── point_farmer.py    Cross-protocol point accumulation

frontend/          Next.js 14 + Tailwind
└── src/app/
    ├── layout.tsx
    └── page.tsx   Dashboard with positions, points, P&L, events
```

## Quick Start

### Backend
```bash
cd backend
uv pip install fastapi uvicorn httpx sse-starlette pydantic pydantic-settings
cd .. && uvicorn backend.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
| Variable | Default | Description |
|---|---|---|
| `SIMULATION_MODE` | `true` | Run in simulation mode |
| `HYPERLIQUID_PRIVATE_KEY` | `` | Private key for live trading |
| `INITIAL_PORTFOLIO_VALUE` | `10000` | Starting portfolio value |
| `MAX_POSITION_PCT` | `0.25` | Max single position size |
| `MAX_DRAWDOWN_PCT` | `0.15` | Max drawdown before halt |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/status` | Agent status and portfolio |
| GET | `/api/positions` | Open positions (perps + DeFi) |
| GET | `/api/points` | Points breakdown per protocol |
| GET | `/api/trades` | Recent trade history |
| POST | `/api/agent/start` | Start the agent |
| POST | `/api/agent/stop` | Stop the agent |
| POST | `/api/agent/resume` | Resume after halt |
| GET | `/api/stream` | SSE live event stream |

## License

MIT
