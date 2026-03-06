# Hyperliquid HyperEVM Airdrop Farming Bot

Simulation-first farming bot for Hyperliquid Season 3 ($HYPE).

## Stack
- FastAPI backend in `backend/`
- Next.js 14 + Tailwind frontend in `frontend/`
- Server-Sent Events dashboard feed

`SIMULATION_MODE=true` by default, so no wallet or API keys are required.

## Features
- Simulated Hyperliquid perps trading
- Simulated HyperEVM DeFi farming across KittenSwap, HypurrFi, and HyperLend
- Cross-protocol point farming across Felix, Mizu, Drip, and Hyperbeat
- Live dashboard with positions, points, P&L trend, score meter, trade log, and event feed

## Run locally

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

## Notes
This repository is simulation-only and intended for educational/testing workflows.
