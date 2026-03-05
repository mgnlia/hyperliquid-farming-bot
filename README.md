# Hyperliquid Farming Bot 🚀

Automated $HYPE Season 3 airdrop farming — perps trading + HyperEVM DeFi.

## Architecture

```
src/
├── main.py                      # FastAPI server (8 REST endpoints + SSE)
├── config.py                    # pydantic-settings (env-driven)
├── database.py                  # Async SQLite (aiosqlite)
├── bot.py                       # Orchestrator — runs all strategies
└── strategies/
    ├── perps_trader.py          # Momentum perps on BTC/ETH/SOL
    ├── hyper_evm_farmer.py      # KittenSwap LP + HyperLend + HypurrFi
    └── points_tracker.py        # Felix/Mizu/Drip/Hyperbeat point tracking

frontend/
├── app/page.tsx                 # Dashboard (P&L chart, points, positions, trades)
├── components/
│   ├── StatusCard.tsx
│   ├── TradeTable.tsx
│   └── PointsPanel.tsx
└── lib/api.ts                   # Typed API client
```

## Strategies

| Strategy | Description | Points Source |
|---|---|---|
| Perps Momentum | Long/short BTC/ETH/SOL on 1h momentum | Felix: 10 pts/trade |
| KittenSwap LP | USDC/HYPE LP position | 8 pts/day |
| HyperLend | USDC lending | 5 pts/day |
| HypurrFi Stake | HYPE staking | 6 pts/day |
| Drip | Daily active bonus | 2 pts/day |
| Hyperbeat | LP actions | 8 pts/LP |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | /health | Health check |
| GET | /api/status | Full bot status + portfolio |
| GET | /api/portfolio | Positions + P&L |
| GET | /api/trades | Recent trades (default 50) |
| GET | /api/points | Points by protocol |
| GET | /api/strategies | Per-strategy status |
| POST | /api/bot/start | Start bot |
| POST | /api/bot/stop | Stop bot |
| GET | /api/stream | SSE real-time events |

## Running locally

```bash
# Backend
pip install uv
uv venv && uv pip install -e ".[dev]"
SIMULATION_MODE=true uvicorn src.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| SIMULATION_MODE | true | Disable live trading |
| HL_WALLET_ADDRESS | "" | Hyperliquid wallet |
| HL_PRIVATE_KEY | "" | Signing key (live mode) |
| MAX_POSITION_USDC | 100 | Max position size |
| DAILY_PERP_TRADES | 5 | Max trades per day |
| NEXT_PUBLIC_API_URL | http://localhost:8000 | Backend URL |

## Deployment

- **Backend**: Railway (Dockerfile)
- **Frontend**: Vercel (Next.js)
