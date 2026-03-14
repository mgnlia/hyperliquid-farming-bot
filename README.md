# Hyperliquid HyperEVM Airdrop Farming Bot

Simulation-first Hyperliquid Season 3 farming bot with a FastAPI backend and Next.js 14 dashboard.

## Features
- `SIMULATION_MODE=true` by default
- Simulated perps farming across BTC, ETH, SOL, and HYPE
- Simulated HyperEVM DeFi allocation management for KittenSwap, HypurrFi, and HyperLend
- Simulated cross-protocol point farming for Felix, Mizu, Drip, and Hyperbeat
- Server-Sent Events feed for live agent activity
- Dashboard with positions, point tracker, score meter, P&L chart, and trade log

## Project structure
- `backend/` – FastAPI app and farming agent
- `frontend/` – Next.js 14 dashboard
- `.github/workflows/ci.yml` – backend Ruff + frontend build CI

## Local development

### Backend
From the repo root:

```bash
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## API
- `GET /health`
- `GET /api/status`
- `GET /api/positions`
- `GET /api/points`
- `GET /api/trades`
- `GET /api/stream`
- `POST /api/agent/start`
- `POST /api/agent/stop`

## Safety
This repository is simulation-only by default and does not require private keys or wallet credentials.
