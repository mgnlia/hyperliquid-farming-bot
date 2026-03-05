"""Main agent loop: orchestrates strategies and emits events."""

import asyncio
import time

from backend.config import settings
from backend.risk import RiskManager
from backend.strategies.perps import PerpsStrategy
from backend.strategies.defi_farming import DeFiFarmingStrategy
from backend.strategies.point_farmer import PointFarmerStrategy


class FarmingAgent:
    """Main farming agent that orchestrates all strategies."""

    def __init__(self):
        self.risk_manager = RiskManager(
            max_position_pct=settings.MAX_POSITION_PCT,
            max_drawdown_pct=settings.MAX_DRAWDOWN_PCT,
            kelly_fraction=settings.KELLY_FRACTION,
        )
        self.perps_strategy = PerpsStrategy()
        self.defi_strategy = DeFiFarmingStrategy()
        self.point_farmer = PointFarmerStrategy()

        self.portfolio_value: float = settings.INITIAL_PORTFOLIO_VALUE
        self.cash: float = settings.INITIAL_PORTFOLIO_VALUE
        self.realized_pnl: float = 0.0
        self.status: str = "stopped"
        self.started_at: float | None = None
        self.events: list[dict] = []
        self._task: asyncio.Task | None = None
        self._event_callbacks: list = []

    def add_event_callback(self, callback):
        self._event_callbacks.append(callback)

    def remove_event_callback(self, callback):
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    async def _emit_event(self, event: dict):
        self.events.append(event)
        if len(self.events) > 500:
            self.events = self.events[-250:]
        for cb in self._event_callbacks:
            try:
                await cb(event)
            except Exception:
                pass

    async def _run_loop(self):
        """Main agent loop."""
        self.status = "running"
        self.started_at = time.time()
        self.risk_manager.peak_value = self.portfolio_value

        await self._emit_event({"type": "agent_started", "portfolio_value": self.portfolio_value, "timestamp": time.time()})

        while self.status == "running":
            try:
                within_limits = self.risk_manager.update_drawdown(self.portfolio_value)
                if not within_limits:
                    await self._emit_event({"type": "risk_halt", "drawdown": self.risk_manager.current_drawdown, "timestamp": time.time()})
                    self.status = "halted"
                    break

                perp_events = self.perps_strategy.execute_signals(self.risk_manager.kelly_size, self.portfolio_value)
                for event in perp_events:
                    if event.get("type") == "close" and "pnl" in event:
                        self.realized_pnl += event["pnl"]
                        self.cash += event["pnl"]
                    await self._emit_event(event)

                defi_events = self.defi_strategy.execute(self.cash * 0.4)
                for event in defi_events:
                    await self._emit_event(event)

                point_events = self.point_farmer.execute()
                for event in point_events:
                    await self._emit_event(event)

                unrealized = self.perps_strategy.get_total_unrealized_pnl()
                defi_earned = self.defi_strategy.get_total_earned()
                self.portfolio_value = self.cash + unrealized + defi_earned

                await self._emit_event({
                    "type": "status_update",
                    "portfolio_value": round(self.portfolio_value, 2),
                    "realized_pnl": round(self.realized_pnl, 2),
                    "unrealized_pnl": round(unrealized, 2),
                    "total_points": round(self.point_farmer.get_total_points(), 2),
                    "airdrop_score": self.point_farmer.get_airdrop_score(),
                    "timestamp": time.time(),
                })

                await asyncio.sleep(settings.AGENT_LOOP_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self._emit_event({"type": "error", "message": str(e), "timestamp": time.time()})
                await asyncio.sleep(settings.AGENT_LOOP_INTERVAL)

    async def start(self):
        if self.status == "running":
            return {"status": "already_running"}
        self._task = asyncio.create_task(self._run_loop())
        return {"status": "started"}

    async def stop(self):
        self.status = "stopped"
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        return {"status": "stopped"}

    async def resume(self):
        if self.status == "halted":
            self.risk_manager.peak_value = self.portfolio_value
            self.risk_manager.current_drawdown = 0.0
        return await self.start()

    def get_status(self) -> dict:
        return {
            "status": self.status,
            "simulation_mode": settings.SIMULATION_MODE,
            "portfolio_value": round(self.portfolio_value, 2),
            "cash": round(self.cash, 2),
            "realized_pnl": round(self.realized_pnl, 2),
            "unrealized_pnl": round(self.perps_strategy.get_total_unrealized_pnl(), 2),
            "defi_earned": round(self.defi_strategy.get_total_earned(), 2),
            "total_points": round(self.point_farmer.get_total_points(), 2),
            "airdrop_score": self.point_farmer.get_airdrop_score(),
            "risk_metrics": self.risk_manager.get_risk_metrics(),
            "started_at": self.started_at,
        }


agent = FarmingAgent()
