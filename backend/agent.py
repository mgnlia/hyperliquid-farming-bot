"""Main async agent loop orchestrating simulated farming strategies."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from .config import settings
from .risk import RiskManager
from .strategies.defi_farming import DefiFarmingStrategy
from .strategies.perps import PerpsStrategy
from .strategies.point_farmer import PointFarmerStrategy


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
        self.state.events = self.state.events[-settings.MAX_EVENTS :]

    def _record_trade(self, trade: dict) -> None:
        self.state.trades.append(trade)
        self.state.trades = self.state.trades[-settings.MAX_TRADES :]

    def _portfolio_value(self) -> float:
        return self.cash + self.perps.unrealized_pnl() + self.defi.total_earned()

    async def _tick(self) -> None:
        previous_tick = self.state.last_tick or time.time()
        now = time.time()
        seconds_elapsed = max(1.0, now - previous_tick)
        self.state.last_tick = now

        self.perps.mark_to_market()
        yield_delta = self.defi.accrue_yield(seconds_elapsed)

        max_notional = self.risk.max_position_notional(self._portfolio_value())
        if self.perps.open_notional() < max_notional and now % 1 < 0.6:
            open_trade = self.perps.maybe_open_position(max_notional - self.perps.open_notional())
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

        for event in self.points.farm_cycle():
            self._emit(event)

        portfolio_value = self._portfolio_value()
        healthy = self.risk.update_drawdown(portfolio_value)
        self._emit(
            {
                "type": "status",
                "timestamp": now,
                "portfolio_value": round(portfolio_value, 4),
                "cash": round(self.cash, 4),
                "realized_pnl": round(self.perps.realized_pnl, 4),
                "unrealized_pnl": round(self.perps.unrealized_pnl(), 4),
                "defi_earned": round(self.defi.total_earned(), 4),
                "yield_delta": round(yield_delta, 6),
                "total_points": round(self.points.total_points(), 4),
                "airdrop_score": round(self.points.airdrop_score(), 4),
                "risk": self.risk.metrics(),
            }
        )

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
        self._emit(
            {
                "type": "agent_started",
                "timestamp": self.state.started_at,
                "simulation_mode": self.simulation_mode,
            }
        )

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
        portfolio_value = self._portfolio_value()
        return {
            "status": self.state.status,
            "simulation_mode": self.simulation_mode,
            "portfolio_value": round(portfolio_value, 4),
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
        return {"perps": self.perps.positions_payload(), "defi": self.defi.positions_payload()}

    def points_payload(self) -> dict:
        return {
            "breakdown": self.points.payload(),
            "total_points": round(self.points.total_points(), 4),
            "airdrop_score": round(self.points.airdrop_score(), 4),
        }

    def trades_payload(self) -> dict:
        return {"trades": self.state.trades}


agent = HyperliquidFarmingAgent()
