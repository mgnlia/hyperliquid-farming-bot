"""FastAPI service exposing bot status, metrics, and controls."""

from __future__ import annotations

import asyncio
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.agent import agent

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
    return {"status": "ok", "service": "hyperliquid-farming-bot"}


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


@app.post("/api/risk/reset")
def reset_risk() -> dict:
    # compatibility endpoint for alternate dashboard clients
    return {"status": "not_applicable_in_simulation_mode"}


async def event_generator():
    last_index = 0
    while True:
        events = agent.state.events
        if last_index < len(events):
            for event in events[last_index:]:
                yield f"data: {json.dumps(event)}\n\n"
            last_index = len(events)

        await asyncio.sleep(1)


@app.get("/api/stream")
async def stream() -> StreamingResponse:
    return StreamingResponse(event_generator(), media_type="text/event-stream")
