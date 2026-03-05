"""FastAPI application with REST endpoints and SSE streaming."""

import asyncio
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from backend.agent import agent

app = FastAPI(title="Hyperliquid Farming Bot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "hyperliquid-farming-bot"}


@app.get("/api/status")
async def get_status():
    return agent.get_status()


@app.get("/api/positions")
async def get_positions():
    return {"perps": agent.perps_strategy.get_positions(), "defi": agent.defi_strategy.get_positions()}


@app.get("/api/points")
async def get_points():
    return {
        "breakdown": agent.point_farmer.get_points_breakdown(),
        "total_points": round(agent.point_farmer.get_total_points(), 2),
        "airdrop_score": agent.point_farmer.get_airdrop_score(),
    }


@app.get("/api/trades")
async def get_trades():
    return {"trades": agent.perps_strategy.get_recent_trades(50)}


@app.post("/api/agent/start")
async def start_agent():
    return await agent.start()


@app.post("/api/agent/stop")
async def stop_agent():
    return await agent.stop()


@app.post("/api/agent/resume")
async def resume_agent():
    return await agent.resume()


@app.get("/api/stream")
async def event_stream():
    async def generate():
        queue: asyncio.Queue = asyncio.Queue()

        async def callback(event: dict):
            await queue.put(event)

        agent.add_event_callback(callback)
        try:
            while True:
                event = await queue.get()
                yield {"event": "message", "data": json.dumps(event)}
        except asyncio.CancelledError:
            pass
        finally:
            agent.remove_event_callback(callback)

    return EventSourceResponse(generate())
