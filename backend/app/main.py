"""FastAPI main — Hyperliquid farming bot API."""
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.database import init_db, get_stats, get_daily_pnl
from app.risk import check_risk
from app.strategies.perp_trader import PerpTrader
from app.strategies.hyperevm_farmer import HyperEVMFarmer
from app.strategies.points_tracker import PointsTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

perp_trader = PerpTrader()
defi_farmer = HyperEVMFarmer()
points_tracker = PointsTracker()
bot_running = False
sse_clients: list = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("DB initialized")
    yield


app = FastAPI(title="Hyperliquid Farming Bot", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if settings.bot_api_key == "changeme-set-BOT_API_KEY-env":
        return True  # dev mode
    if not credentials or credentials.credentials != settings.bot_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


@app.get("/health")
async def health():
    return {"status": "ok", "simulation_mode": settings.simulation_mode, "ts": datetime.utcnow().isoformat()}


@app.get("/api/status")
async def get_status():
    stats = await get_stats()
    daily_pnl = await get_daily_pnl()
    risk = await check_risk()
    return {
        "bot_running": bot_running,
        "simulation_mode": settings.simulation_mode,
        "daily_pnl": daily_pnl,
        "risk": risk,
        "perp": await perp_trader.get_status(),
        "defi": await defi_farmer.get_status(),
        "stats": stats,
    }


@app.get("/api/positions")
async def get_positions():
    from app.database import get_db
    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute("SELECT * FROM trades ORDER BY created_at DESC LIMIT 50") as cursor:
            rows = await cursor.fetchall()
    return {"positions": rows}


@app.get("/api/points")
async def get_points():
    score = await points_tracker.calculate_score()
    return score


@app.get("/api/farm-events")
async def get_farm_events():
    from app.database import get_db
    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute("SELECT * FROM farm_events ORDER BY created_at DESC LIMIT 100") as cursor:
            rows = await cursor.fetchall()
    return {"events": rows}


async def _sse_event_generator() -> AsyncGenerator[str, None]:
    while True:
        stats = await get_stats()
        score = await points_tracker.calculate_score()
        data = {
            "ts": datetime.utcnow().isoformat(),
            "bot_running": bot_running,
            "stats": stats,
            "points": score.get("total_points", 0),
            "tier": score.get("tier", "Bronze"),
        }
        yield f"data: {json.dumps(data)}\n\n"
        await asyncio.sleep(5)


@app.get("/api/stream")
async def sse_stream():
    return StreamingResponse(_sse_event_generator(), media_type="text/event-stream")


@app.post("/api/bot/start", dependencies=[Depends(verify_api_key)])
async def start_bot():
    global bot_running
    if bot_running:
        return {"status": "already_running"}
    bot_running = True
    asyncio.create_task(_run_bot_loop())
    return {"status": "started"}


@app.post("/api/bot/stop", dependencies=[Depends(verify_api_key)])
async def stop_bot():
    global bot_running
    bot_running = False
    return {"status": "stopped"}


async def _run_bot_loop():
    global bot_running
    logger.info("Bot loop started")
    while bot_running:
        try:
            risk = await check_risk()
            if risk["allowed"]:
                await perp_trader.run_volume_farming_cycle()
                await defi_farmer.run_farm_cycle()
            else:
                logger.warning(f"Risk check failed: {risk['reason']}")
        except Exception as e:
            logger.error(f"Bot loop error: {e}")
        await asyncio.sleep(settings.farm_trade_interval_secs)
