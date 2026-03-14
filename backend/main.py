"""FastAPI service exposing farming bot status, metrics, and controls."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .agent import agent
from .config import settings

app = FastAPI(title="Hyperliquid Farming Bot API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    await agent.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await agent.stop()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "hyperliquid-farming-bot", "simulation_mode": settings.SIMULATION_MODE}


@app.get("/api/status")
def get_status() -> dict:
    return agent.status()


@app.get("/api/positions")
def get_positions() -> dict:
    return agent.positions()


@app.get("/api/points")
def get_points() -> dict:
    return agent.points_payload()


@app.get("/api/trades")
def get_trades() -> dict:
    return agent.trades_payload()


@app.post("/api/agent/start")
async def start_agent() -> dict:
    return await agent.start()


@app.post("/api/agent/stop")
async def stop_agent() -> dict:
    return await agent.stop()


async def event_generator() -> AsyncGenerator[str, None]:
    last_index = 0
    while True:
        events = agent.state.events
        if last_index < len(events):
            for event in events[last_index:]:
                yield f"data: {json.dumps(event)}\n\n"
            last_index = len(events)
        else:
            heartbeat = json.dumps({"type": "heartbeat", "timestamp": asyncio.get_event_loop().time()})
            yield f"data: {heartbeat}\n\n"
        await asyncio.sleep(settings.SSE_HEARTBEAT_SECONDS)


@app.get("/api/stream")
async def stream() -> StreamingResponse:
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
