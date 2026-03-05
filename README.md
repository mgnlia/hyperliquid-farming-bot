# Hyperliquid HyperEVM Airdrop Farming Bot

Automated **simulated** Hyperliquid Season 3 farming bot with:

- FastAPI backend (`backend/`)
- Next.js 14 + Tailwind frontend (`frontend/`)
- Server-Sent Events feed for live dashboard updates

> Default mode is `SIMULATION_MODE=true` so no wallet or API keys are required.

## Monorepo layout

```text
backend/
  config.py
  agent.py
  main.py
  strategies/
frontend/
  app/
  components/
  lib/
.github/workflows/ci.yml
```

## Quickstart

### Backend

```bash
cd backend
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## API Endpoints

- `GET /health`
- `GET /api/status`
- `GET /api/positions`
- `GET /api/points`
- `GET /api/trades`
- `GET /api/stream` (SSE)
- `POST /api/agent/start`
- `POST /api/agent/stop`

## Disclaimer

This repository is for simulation and educational use only. It does not execute real trades unless adapted with live credentials and production-grade safeguards.
