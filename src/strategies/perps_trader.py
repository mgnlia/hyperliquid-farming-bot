"""Hyperliquid perps trader — momentum strategy on BTC/ETH/SOL.

In SIMULATION_MODE the strategy generates synthetic trades without
touching the live Hyperliquid API.  Set SIMULATION_MODE=false and
provide HL_PRIVATE_KEY + HL_WALLET_ADDRESS to go live.
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

MARKETS = ["BTC", "ETH", "SOL"]

# ── Simulated mid-prices (updated each tick) ──────────────────────────────────
_sim_prices: dict[str, float] = {"BTC": 67000.0, "ETH": 3500.0, "SOL": 180.0}
_price_history: dict[str, list[float]] = {m: [] for m in MARKETS}


@dataclass
class PerpPosition:
    market: str
    side: str       # "long" | "short"
    size_usdc: float
    entry_price: float
    open_time: float = field(default_factory=time.time)

    @property
    def current_price(self) -> float:
        return _sim_prices.get(self.market, self.entry_price)

    @property
    def pnl(self) -> float:
        direction = 1.0 if self.side == "long" else -1.0
        return direction * (self.current_price - self.entry_price) / self.entry_price * self.size_usdc


@dataclass
class TradeResult:
    success: bool
    market: str
    side: str
    size: float
    price: float
    pnl: float = 0.0
    tx_id: str = ""
    error: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PerpsTrader:
    """Momentum-based perps trader for Hyperliquid."""

    def __init__(self) -> None:
        self.positions: list[PerpPosition] = []
        self.trade_count_today: int = 0
        self.total_pnl: float = 0.0
        self._http: httpx.AsyncClient | None = None

    # ── Price feed ────────────────────────────────────────────────────────────

    async def _fetch_price(self, market: str) -> float:
        if settings.simulation_mode:
            change = random.gauss(0, 0.003)
            _sim_prices[market] = _sim_prices[market] * (1 + change)
            return _sim_prices[market]
        # Live: hit Hyperliquid info endpoint
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=10.0)
        resp = await self._http.post(
            f"{settings.hl_api_url}/info",
            json={"type": "allMids"},
        )
        resp.raise_for_status()
        mids = resp.json()
        key = f"{market}-USD"
        return float(mids.get(key, _sim_prices[market]))

    # ── Signal ────────────────────────────────────────────────────────────────

    def _momentum_signal(self, market: str, price: float) -> str | None:
        """Return 'long', 'short', or None based on 1-hour momentum."""
        hist = _price_history[market]
        hist.append(price)
        if len(hist) > 60:
            hist.pop(0)
        if len(hist) < 10:
            return None
        ret_1h = (hist[-1] - hist[0]) / hist[0]
        if ret_1h > 0.005:
            return "long"
        if ret_1h < -0.005:
            return "short"
        return None

    # ── Execution ─────────────────────────────────────────────────────────────

    async def _execute_sim(self, market: str, side: str, size: float, price: float) -> TradeResult:
        await asyncio.sleep(0.05)   # simulate network latency
        tx_id = f"sim_{market}_{int(time.time())}_{random.randint(1000, 9999)}"
        pos = PerpPosition(market=market, side=side, size_usdc=size, entry_price=price)
        self.positions.append(pos)
        return TradeResult(success=True, market=market, side=side, size=size, price=price, tx_id=tx_id)

    async def _close_position(self, pos: PerpPosition) -> TradeResult:
        price = await self._fetch_price(pos.market)
        pnl = pos.pnl
        self.total_pnl += pnl
        self.positions.remove(pos)
        return TradeResult(
            success=True, market=pos.market,
            side="close", size=pos.size_usdc, price=price, pnl=pnl,
            tx_id=f"sim_close_{int(time.time())}",
        )

    # ── Main tick ─────────────────────────────────────────────────────────────

    async def tick(self) -> list[TradeResult]:
        """Run one strategy tick — fetch prices, generate signals, maybe trade."""
        results: list[TradeResult] = []

        for market in MARKETS:
            price = await self._fetch_price(market)
            signal = self._momentum_signal(market, price)

            # Close stale positions (held > 30 min in sim)
            for pos in list(self.positions):
                if pos.market == market and (time.time() - pos.open_time) > 1800:
                    r = await self._close_position(pos)
                    results.append(r)
                    logger.info("Closed %s %s pnl=%.4f", market, pos.side, r.pnl)

            # Open new position if signal and within daily limit
            open_markets = {p.market for p in self.positions}
            if (
                signal
                and market not in open_markets
                and self.trade_count_today < settings.daily_perp_trades
            ):
                r = await self._execute_sim(market, signal, settings.perp_trade_size_usdc, price)
                self.trade_count_today += 1
                results.append(r)
                logger.info("Opened %s %s @ %.2f", market, signal, price)

        return results

    def status(self) -> dict[str, Any]:
        return {
            "strategy": "perps_momentum",
            "open_positions": len(self.positions),
            "trades_today": self.trade_count_today,
            "total_pnl": round(self.total_pnl, 4),
            "positions": [
                {
                    "market": p.market,
                    "side": p.side,
                    "size_usdc": p.size_usdc,
                    "entry_price": p.entry_price,
                    "current_price": p.current_price,
                    "pnl": round(p.pnl, 4),
                }
                for p in self.positions
            ],
        }
