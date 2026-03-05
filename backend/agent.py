"""Main async agent loop orchestrating strategy execution."""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field

from backend.config import settings
from backend.risk import RiskManager
from backend.strategies.defi_farming import DefiFarmingStrategy
from backend.strategies.perps import PerpsStrategy
from backend.strategies.point_farmer import PointFarmerStrategy


@dataclass
class AgentState:
    status: str = "stopped"
    started_at: float | None = None
    last_tick: float | None = None
    events: list[dict] = field(default_factory=list)
    trades: list[dict] = field(default_factory=list)


class HyperliquidFarmingAgent:
    def __init__(self):
        self.simulation_mode = settings.SIMULATION_MODE
        self.loop_interval = settings.AGENT_LOOP_INTERVAL

        self.perps = PerpsStrategy()
        self.defi = DefiFarmingStrategy()
        self.points = PointFarmerStrategy()
        self.risk = RiskManager(settings.MAX_POSITION_PCT, settings.MAX_DRAWDOWN_PCT, settings.KELLY_FRACTION)

        self.state = AgentState()
        self.cash = settings.INITIAL_PORTFOLIO_VALUE

        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    def _emit(self, event: dict) -> None:
        self.state.events.append(event)
        self.state.events = self.state.events[-300:]

    def _record_trade(self, trade: dict) -> None:
        self.state.trades.append(trade)
        self.state.trades = self.state.trades[-300:]

    def _portfolio_value(self) -> float:
        return self.cash + self.perps.unrealized_pnl() + self.defi.total_earned()

    def _max_position_notional(self) -> float:
        value = max(1.0, self._portfolio_value())
        return value * settings.MAX_POSITION_PCT

    async def _tick(self) -> None:
        started = self.state.last_tick or time.time()
        now = time.time()
        dt = max(1.0, now - started)
        self.state.last_tick = now

        self.perps.mark_to_market()
        yield_delta = self.defi.accrue_yield(dt)

        if random.random() < 0.55:
            open_trade = self.perps.maybe_open_position(self._max_position_notional())
            if open_trade:
                self._record_trade(open_trade)
                self._emit(open_trade)

        close_trade = self.perps.maybe_close_position()
        if close_trade:
            self.cash += close_trade.get("pnl", 0.0)
            self._record_trade(close_trade)
            self._emit(close_trade)

        rebalance_event = self.defi.rebalance()
        if rebalance_event:
            self._emit(rebalance_event)

        points_events = self.points.farm_cycle()
        for event in points_events:
            self._emit(event)

        value = self._portfolio_value()
        healthy = self.risk.update_drawdown(value)

        status_event = {
            "type": "status",
            "timestamp": now,
            "portfolio_value": round(value, 4),
            "realized_pnl": round(self.perps.realized_pnl, 4),
            "unrealized_pnl": round(self.perps.unrealized_pnl(), 4),
            "defi_earned": round(self.defi.total_earned(), 4),
            "yield_delta": round(yield_delta, 6),
            "total_points": round(self.points.total_points(), 4),
            "airdrop_score": round(self.points.airdrop_score(), 4),
            "risk": self.risk.metrics(),
        }
        self._emit(status_event)

        if not healthy:
            self.state.status = "halted"
            self._emit(
                {
                    "type": "risk_halt",
                    "timestamp": now,
                    "reason": "Max drawdown exceeded",
                    "drawdown": self.risk.current_drawdown,
                }
            )
            self._stop_event.set()

    async def _run(self) -> None:
        self.state.status = "running"
        self.state.started_at = time.time()
        self.state.last_tick = self.state.started_at
        self._stop_event.clear()

        self._emit({"type": "agent_started", "timestamp": self.state.started_at, "simulation_mode": self.simulation_mode})

        while not self._stop_event.is_set():
            await self._tick()
            await asyncio.sleep(self.loop_interval)

        if self.state.status != "halted":
            self.state.status = "stopped"
        self._emit({"type": "agent_stopped", "timestamp": time.time()})

    async def start(self) -> dict:
        if self._task and not self._task.done():
            return {"status": self.state.status}

        self._task = asyncio.create_task(self._run())
        return {"status": "running"}

    async def stop(self) -> dict:
        if self._task and not self._task.done():
            self._stop_event.set()
            await self._task
        self.state.status = "stopped"
        return {"status": self.state.status}

    def status(self) -> dict:
        value = self._portfolio_value()
        return {
            "status": self.state.status,
            "simulation_mode": self.simulation_mode,
            "portfolio_value": round(value, 4),
            "cash": round(self.cash, 4),
            "realized_pnl": round(self.perps.realized_pnl, 4),
            "unrealized_pnl": round(self.perps.unrealized_pnl(), 4),
            "defi_earned": round(self.defi.total_earned(), 4),
            "total_points": round(self.points.total_points(), 4),
            "airdrop_score": round(self.points.airdrop_score(), 4),
            "risk_metrics": self.risk.metrics(),
            "started_at": self.state.started_at,
        }

    def positions(self) -> dict:
        return {
            "perps": self.perps.positions_payload(),
            "defi": self.defi.positions_payload(),
        }

    def points_payload(self) -> dict:
        return {
            "breakdown": self.points.payload(),
            "total_points": round(self.points.total_points(), 4),
            "airdrop_score": round(self.points.airdrop_score(), 4),
        }

    def trades_payload(self) -> dict:
        return {"trades": self.state.trades}


agent = HyperliquidFarmingAgent()
