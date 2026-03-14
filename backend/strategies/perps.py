"""Simulated Hyperliquid perps strategy."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

SYMBOLS = ["BTC", "ETH", "SOL", "HYPE"]


@dataclass
class PerpPosition:
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    opened_at: float

    @property
    def unrealized_pnl(self) -> float:
        direction = 1 if self.side == "long" else -1
        return (self.current_price - self.entry_price) * self.size * direction

    @property
    def notional(self) -> float:
        return self.current_price * self.size


class PerpsStrategy:
    def __init__(self):
        self.positions: list[PerpPosition] = []
        self.realized_pnl = 0.0
        self._price_state = {"BTC": 72000.0, "ETH": 3600.0, "SOL": 180.0, "HYPE": 35.0}

    def _price(self, symbol: str) -> float:
        base = self._price_state[symbol]
        drift = random.uniform(-0.02, 0.02)
        next_price = max(0.01, base * (1 + drift))
        self._price_state[symbol] = next_price
        return next_price

    def maybe_open_position(self, max_notional: float) -> dict | None:
        if len(self.positions) >= 6:
            return None

        symbol = random.choice(SYMBOLS)
        side = random.choice(["long", "short"])
        price = self._price(symbol)
        notional = max_notional * random.uniform(0.25, 0.8)
        size = max(0.0001, notional / price)

        position = PerpPosition(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=price,
            current_price=price,
            opened_at=time.time(),
        )
        self.positions.append(position)

        return {
            "type": "perp_open",
            "symbol": symbol,
            "side": side,
            "size": round(size, 6),
            "notional": round(notional, 4),
            "price": round(price, 4),
            "timestamp": time.time(),
        }

    def maybe_close_position(self) -> dict | None:
        if not self.positions or random.random() < 0.55:
            return None

        index = random.randrange(len(self.positions))
        position = self.positions[index]
        exit_price = self._price(position.symbol)
        position.current_price = exit_price
        pnl = position.unrealized_pnl
        self.realized_pnl += pnl
        closed = self.positions.pop(index)

        return {
            "type": "perp_close",
            "symbol": closed.symbol,
            "side": closed.side,
            "size": round(closed.size, 6),
            "entry_price": round(closed.entry_price, 4),
            "exit_price": round(exit_price, 4),
            "pnl": round(pnl, 4),
            "timestamp": time.time(),
        }

    def mark_to_market(self) -> None:
        for position in self.positions:
            position.current_price = self._price(position.symbol)

    def unrealized_pnl(self) -> float:
        return sum(position.unrealized_pnl for position in self.positions)

    def open_notional(self) -> float:
        return sum(position.notional for position in self.positions)

    def positions_payload(self) -> list[dict]:
        return [
            {
                "symbol": position.symbol,
                "side": position.side,
                "size": round(position.size, 6),
                "entry_price": round(position.entry_price, 4),
                "current_price": round(position.current_price, 4),
                "unrealized_pnl": round(position.unrealized_pnl, 4),
                "notional": round(position.notional, 4),
                "opened_at": position.opened_at,
            }
            for position in self.positions
        ]
