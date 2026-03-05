# ⚡ Hyperliquid Farming Bot — $HYPE Season 3

Automated airdrop farming for Hyperliquid: perps trading, DeFi yield, and cross-protocol point accumulation.

## Architecture

```
backend (FastAPI + uv)
├── src/
│   ├── config.py              # Pydantic-settings, all env vars
│   ├── database.py            # SQLite with hash-chained audit log
│   ├── risk.py                # Position limits, drawdown protection
│   ├── main.py                # FastAPI: /api/status /api/stream (SSE) etc.
│   ├── bot/orchestrator.py    # Asyncio task manager
│   └── strategies/
│       ├── perps.py           # Perps trading via Hyperliquid SDK
│       ├── defi_farming.py    # KittenSwap LP, HypurrFi, HyperLend
│       └── point_farmer.py    # Felix, Mizu, Drip, Hyperbeat points

frontend (Next.js 14 + Tailwind)
└── app/
    ├── page.tsx               # Main dashboard
    └── components/
        ├── StatCard.tsx
        ├── AirdropScore.tsx   # Score meter with checklist
        ├── PointsPanel.tsx    # Per-protocol points bars
        ├── PositionsTable.tsx # Risk + positions
        ├── PnLChart.tsx       # Cumulative volume chart
        ├── TradeHistory.tsx   # Trade log table
        └── BotControls.tsx    # Start/Stop/Reset
```

## Quick Start

```bash
# Backend
cp .env.example .env
# Edit .env — set PRIVATE_KEY, WALLET_ADDRESS, SIMULATION_MODE=true

uv pip install -e ".[dev]"
python -m src.main
# → http://localhost:8000

# Frontend
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
# → http://localhost:3000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/status` | Full bot status |
| GET | `/api/strategies` | Per-strategy status |
| GET | `/api/positions` | Risk + positions |
| GET | `/api/points` | Protocol points breakdown |
| GET | `/api/trades?limit=50` | Trade history |
| GET | `/api/airdrop` | Airdrop readiness score |
| GET | `/api/stream` | SSE real-time feed |
| POST | `/api/bot/start` | Start bot |
| POST | `/api/bot/stop` | Stop bot |
| POST | `/api/risk/reset` | Clear risk block |

## Strategies

### 1. Perps Trading (`ENABLE_PERPS=true`)
- Trades BTC, ETH, SOL, ARB, AVAX perpetuals
- Generates volume for native Hyperliquid points
- Configurable trade size and interval

### 2. DeFi Farming (`ENABLE_DEFI=true`)
- **KittenSwap** — LP positions (~35% APY)
- **HypurrFi** — HYPE staking (~18% APY)
- **HyperLend** — Lending supply (~8% APY)

### 3. Point Farming (`ENABLE_POINTS=true`)
- **Felix** — CDP protocol (2× multiplier)
- **Mizu** — Liquid staking (1.8× multiplier)
- **Drip** — Yield aggregator (1.5× multiplier)
- **Hyperbeat** — Structured vaults (1.6× multiplier)
- **Hyperliquid Native** — DEX trading (3× multiplier)

## Risk Management

- Per-asset position limit (`MAX_POSITION_USD`, default $500)
- Total exposure limit (`MAX_TOTAL_EXPOSURE_USD`, default $2,000)
- Max drawdown circuit breaker (`MAX_DRAWDOWN_PCT`, default 10%)
- Max leverage cap (`MAX_LEVERAGE`, default 3×)
- Auto-block on limit breach; manual reset via API

## Airdrop Score

The dashboard computes a 0–100 readiness score:
- ✓ $1,000+ trading volume
- ✓ 2+ active DeFi positions
- ✓ 100+ protocol points
- ✓ 3+ protocols active
- ✓ 50+ total trades

## Deployment (Railway)

```bash
# Set environment variables in Railway dashboard:
SIMULATION_MODE=false
PRIVATE_KEY=<your-key>
WALLET_ADDRESS=<your-address>

railway up
```

## ⚠ Disclaimer

This software is for educational purposes. Trading involves significant risk. Always start with `SIMULATION_MODE=true`. Never commit private keys. DYOR.
