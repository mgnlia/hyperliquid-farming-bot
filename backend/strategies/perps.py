"""Perpetual futures trading strategy for Hyperliquid HIP-3 markets."""

import random
import time
from dataclasses import dataclass, field


@dataclass
class PerpPosition:
    """Represents an open perpetual position."""

    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    opened_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "size": round(self.size, 4),
            "entry_price": round(self.entry_price, 2),
            "current_price": round(self.current_price, 2),
            "unrealized_pnl": round(self.unrealized_pnl, 2),
            "opened_at": self.opened_at,
        }


SIMULATED_MARKETS = [
    {"symbol": "ETH-PERP", "base_price": 3200.0, "volatility": 0.02},
    {"symbol": "BTC-PERP", "base_price": 95000.0, "volatility": 0.015},
    {"symbol": "HYPE-PERP", "base_price": 28.0, "volatility": 0.04},
    {"symbol": "ARB-PERP", "base_price": 1.10, "volatility": 0.03},
    {"symbol": "SOL-PERP", "base_price": 180.0, "volatility": 0.025},
    {"symbol": "PURR-PERP", "base_price": 0.45, "volatility": 0.06},
]


class PerpsStrategy:
    """Simulated perpetual futures trading strategy."""

    def __init__(self):
        self.positions: list[PerpPosition] = []
        self.prices: dict[str, float] = {}
        self.trade_history: list[dict] = []
        self._init_prices()

    def _init_prices(self):
        for market in SIMULATED_MARKETS:
            self.prices[market["symbol"]] = market["base_price"]

    def update_prices(self):
        """Simulate price movements."""
        for market in SIMULATED_MARKETS:
            symbol = market["symbol"]
            vol = market["volatility"]
            change = random.gauss(0, vol)
            current = self.prices.get(symbol, market["base_price"])
            new_price = current * (1 + change)
            self.prices[symbol] = max(new_price, market["base_price"] * 0.5)

    def generate_signal(self, symbol: str) -> dict:
        """Generate a simulated trading signal."""
        momentum = random.uniform(-1, 1)
        strength = abs(momentum)
        if strength < 0.3:
            return {"action": "hold", "symbol": symbol, "strength": 0.0}
        side = "long" if momentum > 0 else "short"
        return {
            "action": "open",
            "symbol": symbol,
            "side": side,
            "strength": round(strength, 3),
            "win_prob": round(0.45 + strength * 0.15, 3),
            "win_loss_ratio": round(1.2 + strength * 0.8, 3),
        }

    def execute_signals(self, kelly_size_fn, portfolio_value: float) -> list[dict]:
        """Run strategy: update prices, generate signals, execute trades."""
        self.update_prices()
        events = []

        for pos in self.positions:
            pos.current_price = self.prices.get(pos.symbol, pos.entry_price)
            if pos.side == "long":
                pos.unrealized_pnl = (pos.current_price - pos.entry_price) * pos.size
            else:
                pos.unrealized_pnl = (pos.entry_price - pos.current_price) * pos.size

        closed = []
        for pos in self.positions:
            pnl_pct = pos.unrealized_pnl / (pos.entry_price * pos.size) if pos.size > 0 else 0
            if pnl_pct > 0.03 or pnl_pct < -0.02 or random.random() < 0.1:
                trade = {
                    "type": "close",
                    "symbol": pos.symbol,
                    "side": pos.side,
                    "size": pos.size,
                    "entry_price": pos.entry_price,
                    "exit_price": pos.current_price,
                    "pnl": round(pos.unrealized_pnl, 2),
                    "timestamp": time.time(),
                }
                self.trade_history.append(trade)
                events.append(trade)
                closed.append(pos)

        for pos in closed:
            self.positions.remove(pos)

        if len(self.positions) < 3:
            market = random.choice(SIMULATED_MARKETS)
            signal = self.generate_signal(market["symbol"])
            if signal["action"] == "open":
                size_pct = kelly_size_fn(signal["win_prob"], signal["win_loss_ratio"])
                if size_pct > 0:
                    position_value = portfolio_value * size_pct
                    price = self.prices[signal["symbol"]]
                    size = position_value / price
                    pos = PerpPosition(
                        symbol=signal["symbol"],
                        side=signal["side"],
                        size=size,
                        entry_price=price,
                        current_price=price,
                    )
                    self.positions.append(pos)
                    trade = {
                        "type": "open",
                        "symbol": pos.symbol,
                        "side": pos.side,
                        "size": round(pos.size, 4),
                        "price": round(price, 2),
                        "timestamp": time.time(),
                    }
                    self.trade_history.append(trade)
                    events.append(trade)

        return events

    def get_positions(self) -> list[dict]:
        return [p.to_dict() for p in self.positions]

    def get_total_unrealized_pnl(self) -> float:
        return sum(p.unrealized_pnl for p in self.positions)

    def get_recent_trades(self, limit: int = 50) -> list[dict]:
        return self.trade_history[-limit:]
