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


class PerpsStrategy:
    def __init__(self):
        self.positions: list[PerpPosition] = []
        self.realized_pnl: float = 0.0
        self._price_state = {"BTC": 72000.0, "ETH": 3600.0, "SOL": 180.0, "HYPE": 35.0}

    def _price(self, symbol: str) -> float:
        base = self._price_state[symbol]
        drift = random.uniform(-0.02, 0.02)
        nxt = max(0.01, base * (1 + drift))
        self._price_state[symbol] = nxt
        return nxt

    def maybe_open_position(self, max_notional: float) -> dict | None:
        if len(self.positions) >= 6:
            return None

        symbol = random.choice(SYMBOLS)
        side = random.choice(["long", "short"])
        price = self._price(symbol)

        # randomize size with mild preference for smaller risk
        notional = max_notional * random.uniform(0.3, 1.0)
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
            "price": round(price, 4),
            "timestamp": time.time(),
        }

    def maybe_close_position(self) -> dict | None:
        if not self.positions or random.random() < 0.55:
            return None

        idx = random.randrange(len(self.positions))
        pos = self.positions[idx]
        exit_price = self._price(pos.symbol)
        pos.current_price = exit_price

        pnl = pos.unrealized_pnl
        self.realized_pnl += pnl

        closed = self.positions.pop(idx)

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
        for pos in self.positions:
            pos.current_price = self._price(pos.symbol)

    def unrealized_pnl(self) -> float:
        return sum(pos.unrealized_pnl for pos in self.positions)

    def positions_payload(self) -> list[dict]:
        return [
            {
                "symbol": p.symbol,
                "side": p.side,
                "size": round(p.size, 6),
                "entry_price": round(p.entry_price, 4),
                "current_price": round(p.current_price, 4),
                "unrealized_pnl": round(p.unrealized_pnl, 4),
                "opened_at": p.opened_at,
            }
            for p in self.positions
        ]
