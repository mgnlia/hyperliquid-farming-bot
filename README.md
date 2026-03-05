# Hyperliquid HyperEVM Airdrop Farming Bot — $HYPE Season 3

Automated farming bot for Hyperliquid Season 3 airdrop. Trades perps + farms DeFi protocols on HyperEVM to maximize $HYPE allocation.

## Architecture

- **Backend**: FastAPI (Python/uv) — strategies, risk management, SQLite persistence
- **Frontend**: Next.js 14 + Tailwind — live dashboard with SSE updates

## Strategies

1. **Perp Trading** — Equity perps via Hyperliquid SDK (volume farming for trading score)
2. **HyperEVM DeFi** — KittenSwap LP, HypurrFi staking, HyperLend lending
3. **Cross-Protocol** — Felix, Mizu, Drip, Hyperbeat point farming
4. **Points Tracker** — Estimates airdrop tier & HYPE allocation

## Quick Start

```bash
# Backend
cd backend
uv sync
SIMULATION_MODE=true uv run uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| SIMULATION_MODE | true | Run without real wallet |
| PRIVATE_KEY | — | Wallet private key (live mode) |
| WALLET_ADDRESS | — | Wallet address |
| BOT_API_KEY | changeme | API auth key for bot control |
| DAILY_LOSS_LIMIT_USD | 100 | Hard daily loss limit |
| PERP_TRADE_SIZE_USD | 50 | Per-trade size |

## API Endpoints

- `GET /health` — Health check
- `GET /api/status` — Bot status + stats
- `GET /api/positions` — Trade history
- `GET /api/points` — Airdrop score estimate
- `GET /api/farm-events` — DeFi farming history
- `GET /api/stream` — SSE real-time updates
- `POST /api/bot/start` — Start bot (requires BOT_API_KEY)
- `POST /api/bot/stop` — Stop bot (requires BOT_API_KEY)

## Season 3 Context

Hyperliquid has 38.8% of $HYPE supply still reserved for future distributions. Season 1 distributed ~31M HYPE to ~94K addresses. This bot maximizes eligibility by:
- Generating consistent trading volume across perp markets
- Interacting with multiple HyperEVM DeFi protocols
- Maintaining daily activity streaks
