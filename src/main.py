"""FastAPI entrypoint — all REST + SSE endpoints."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from src.bot import bot
from src.config import settings
from src.database import get_points_summary, get_trades

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Hyperliquid Farming Bot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Lifecycle ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup() -> None:
    logger.info("Starting bot in simulation_mode=%s", settings.simulation_mode)
    await bot.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    await bot.stop()


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "bot": bot.state.status}


# ── Status ────────────────────────────────────────────────────────────────────

@app.get("/api/status")
async def api_status() -> dict:
    return bot.full_status()


# ── Portfolio ─────────────────────────────────────────────────────────────────

@app.get("/api/portfolio")
async def api_portfolio() -> dict:
    perps_status = bot.perps.status()
    farming_status = bot.farmer.status()
    return {
        "total_pnl": round(bot.state.total_pnl, 4),
        "total_tvl": farming_status["total_tvl"],
        "open_perp_positions": perps_status["open_positions"],
        "perp_positions": perps_status["positions"],
        "farm_positions": farming_status["positions"],
    }


# ── Trades ────────────────────────────────────────────────────────────────────

@app.get("/api/trades")
async def api_trades(limit: int = 50) -> dict:
    trades = await get_trades(limit)
    return {"trades": trades, "count": len(trades)}


# ── Points ────────────────────────────────────────────────────────────────────

@app.get("/api/points")
async def api_points() -> dict:
    db_summary = await get_points_summary()
    live_summary = bot.points.summary()
    return {
        "grand_total": round(bot.points.grand_total, 2),
        "by_protocol": live_summary,
        "db_summary": db_summary,
    }


# ── Strategies ────────────────────────────────────────────────────────────────

@app.get("/api/strategies")
async def api_strategies() -> dict:
    return {
        "perps": bot.perps.status(),
        "farming": bot.farmer.status(),
        "points_tracker": {
            "grand_total": round(bot.points.grand_total, 2),
            "protocols": list(bot.points.protocols.keys()),
        },
    }


# ── Bot control ───────────────────────────────────────────────────────────────

@app.post("/api/bot/start")
async def api_bot_start() -> dict:
    await bot.start()
    return {"status": bot.state.status}


@app.post("/api/bot/stop")
async def api_bot_stop() -> dict:
    await bot.stop()
    return {"status": bot.state.status}


# ── SSE stream ────────────────────────────────────────────────────────────────

async def _event_generator() -> AsyncGenerator[str, None]:
    last_idx = 0
    while True:
        events = bot.state.events
        new = events[last_idx:]
        for ev in new:
            yield f"data: {json.dumps(ev)}\n\n"
        last_idx = len(events)
        await asyncio.sleep(1)


@app.get("/api/stream")
async def api_stream() -> StreamingResponse:
    return StreamingResponse(_event_generator(), media_type="text/event-stream")
