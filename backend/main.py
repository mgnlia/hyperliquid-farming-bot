"""FastAPI application with REST endpoints and SSE streaming."""

import asyncio
import json
import secrets
from collections import deque

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sse_starlette.sse import EventSourceResponse

from backend.agent import agent
from backend.config import settings

app = FastAPI(title="Hyperliquid Farming Bot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bearer = HTTPBearer(auto_error=False)


def _require_api_key(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> None:
    """Validate Bearer token. Skipped when BOT_API_KEY is empty (dev/CI mode)."""
    if not settings.BOT_API_KEY:
        return  # auth disabled
    if credentials is None or not secrets.compare_digest(credentials.credentials, settings.BOT_API_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@app.get("/health")
async def health():
    """Health check — no auth required."""
    return {"status": "ok", "service": "hyperliquid-farming-bot"}


@app.get("/api/status", dependencies=[Depends(_require_api_key)])
async def get_status():
    return agent.get_status()


@app.get("/api/positions", dependencies=[Depends(_require_api_key)])
async def get_positions():
    return {"perps": agent.perps_strategy.get_positions(), "defi": agent.defi_strategy.get_positions()}


@app.get("/api/points", dependencies=[Depends(_require_api_key)])
async def get_points():
    return {
        "breakdown": agent.point_farmer.get_points_breakdown(),
        "total_points": round(agent.point_farmer.get_total_points(), 2),
        "airdrop_score": agent.point_farmer.get_airdrop_score(),
    }


@app.get("/api/trades", dependencies=[Depends(_require_api_key)])
async def get_trades():
    return {"trades": agent.perps_strategy.get_recent_trades(50)}


@app.post("/api/agent/start", dependencies=[Depends(_require_api_key)])
async def start_agent():
    return await agent.start()


@app.post("/api/agent/stop", dependencies=[Depends(_require_api_key)])
async def stop_agent():
    return await agent.stop()


@app.post("/api/agent/resume", dependencies=[Depends(_require_api_key)])
async def resume_agent():
    return await agent.resume()


@app.get("/api/stream")
async def event_stream(request: Request):
    """SSE live event stream.

    Uses a bounded asyncio.Queue per subscriber — safe when the event buffer
    is trimmed (old approach of slicing a list would kill existing iterators).
    """

    async def generate():
        # Bounded queue: drop oldest if subscriber is too slow
        queue: asyncio.Queue = asyncio.Queue(maxsize=200)

        async def callback(event: dict):
            if queue.full():
                try:
                    queue.get_nowait()  # drop oldest
                except asyncio.QueueEmpty:
                    pass
            await queue.put(event)

        agent.add_event_callback(callback)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {"event": "message", "data": json.dumps(event)}
                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield {"event": "ping", "data": "{}"}
        except asyncio.CancelledError:
            pass
        finally:
            agent.remove_event_callback(callback)

    return EventSourceResponse(generate())
