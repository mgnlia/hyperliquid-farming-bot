"""Main bot orchestrator — runs all strategies in a loop."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from src.config import settings
from src.database import init_db, insert_points, insert_trade
from src.strategies.hyper_evm_farmer import HyperEVMFarmer
from src.strategies.perps_trader import PerpsTrader
from src.strategies.points_tracker import PointsTracker

logger = logging.getLogger(__name__)


class BotState:
    def __init__(self) -> None:
        self.status: str = "stopped"
        self.started_at: str = ""
        self.total_pnl: float = 0.0
        self.total_points: float = 0.0
        self.tick_count: int = 0
        self.last_tick: str = ""
        self.events: list[dict[str, Any]] = []

    def emit(self, event_type: str, message: str, data: dict[str, Any] | None = None) -> None:
        entry = {
            "type": event_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        }
        self.events.append(entry)
        if len(self.events) > 500:
            self.events = self.events[-500:]
        logger.info("[%s] %s", event_type, message)


class HyperBot:
    """Top-level bot that orchestrates all three strategies."""

    def __init__(self) -> None:
        self.perps = PerpsTrader()
        self.farmer = HyperEVMFarmer()
        self.points = PointsTracker()
        self.state = BotState()
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            return
        await init_db()
        self._running = True
        self.state.status = "running"
        self.state.started_at = datetime.now(timezone.utc).isoformat()
        self.state.emit("bot", f"Bot started — simulation={settings.simulation_mode}")
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        self.state.status = "stopped"
        if self._task:
            self._task.cancel()
        self.state.emit("bot", "Bot stopped")

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._tick()
            except Exception as exc:
                self.state.emit("error", f"Tick error: {exc}")
                logger.exception("Tick failed")
            await asyncio.sleep(settings.loop_interval_seconds)

    async def _tick(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.state.tick_count += 1
        self.state.last_tick = now

        # 1. Perps trading
        perp_results = await self.perps.tick()
        for r in perp_results:
            if r.success:
                await insert_trade(r.timestamp, "perps", r.market, r.side, r.size, r.price, r.pnl)
                self.state.total_pnl += r.pnl
                self.state.emit("trade", f"{r.side.upper()} {r.market} @ {r.price:.2f}", {"pnl": r.pnl})
                if r.side in ("long", "short"):
                    self.points.record_trade("Felix")

        # 2. HyperEVM farming
        farm_events = await self.farmer.tick()
        for ev in farm_events:
            if ev.get("event") == "points_accrued":
                proto = ev["protocol"]
                earned = ev["earned"]
                cumulative = ev["cumulative"]
                await insert_points(now, proto, earned, cumulative)
                self.points.record_lp(proto) if proto == "KittenSwap" else None
                self.points.record_deposit(proto) if proto == "HyperLend" else None
                self.points.record_stake(proto) if proto == "HypurrFi" else None

        # 3. Daily points tick (scaled to loop interval)
        tick_fraction = settings.loop_interval_seconds / 86400.0
        for name, pp in self.points.protocols.items():
            from src.strategies.points_tracker import PROTOCOL_RATES
            rate = PROTOCOL_RATES[name].get("per_day_active", 0.0) * tick_fraction
            if rate > 0:
                pp.add("daily_active_tick", rate)
                await insert_points(now, name, rate, pp.total)

        self.state.total_points = self.points.grand_total

    def full_status(self) -> dict[str, Any]:
        return {
            "bot": {
                "status": self.state.status,
                "simulation_mode": settings.simulation_mode,
                "started_at": self.state.started_at,
                "tick_count": self.state.tick_count,
                "last_tick": self.state.last_tick,
                "total_pnl": round(self.state.total_pnl, 4),
                "total_points": round(self.state.total_points, 2),
            },
            "perps": self.perps.status(),
            "farming": self.farmer.status(),
            "points": self.points.summary(),
        }


# Singleton
bot = HyperBot()
