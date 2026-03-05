# Hyperliquid Farming Bot Backend

FastAPI backend for **simulated** Hyperliquid + HyperEVM Season 3 farming.

## Features
- `SIMULATION_MODE=true` default (no wallet required)
- Simulated perps strategy
- Simulated DeFi strategy (KittenSwap, HypurrFi, HyperLend)
- Simulated cross-protocol points farming (Felix, Mizu, Drip, Hyperbeat)
- SSE event stream for live dashboard updates

## Run locally
```bash
cd backend
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints
- `GET /health`
- `GET /api/status`
- `GET /api/positions`
- `GET /api/points`
- `GET /api/trades`
- `GET /api/stream` (SSE)
- `POST /api/agent/start`
- `POST /api/agent/stop`
