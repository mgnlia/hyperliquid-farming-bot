"""Cross-protocol points tracker.

Tracks estimated airdrop points earned across Felix, Mizu, Drip, Hyperbeat,
plus any other protocol registered at runtime.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Points awarded per qualifying action per protocol
PROTOCOL_RATES: dict[str, dict[str, float]] = {
    "Felix": {
        "per_trade": 10.0,
        "per_borrow_usdc": 0.05,   # per USDC borrowed
        "per_day_active": 2.0,
    },
    "Mizu": {
        "per_deposit": 5.0,
        "per_day_active": 1.0,
    },
    "Drip": {
        "per_day_active": 2.0,
        "per_referral": 50.0,
    },
    "Hyperbeat": {
        "per_lp_action": 8.0,
        "per_day_active": 3.0,
    },
    "KittenSwap": {
        "per_lp_action": 8.0,
        "per_day_active": 2.0,
    },
    "HyperLend": {
        "per_deposit": 5.0,
        "per_day_active": 1.5,
    },
    "HypurrFi": {
        "per_stake": 6.0,
        "per_day_active": 2.0,
    },
}


@dataclass
class ProtocolPoints:
    protocol: str
    total: float = 0.0
    events: list[dict[str, Any]] = field(default_factory=list)

    def add(self, reason: str, amount: float) -> None:
        self.total += amount
        self.events.append({
            "reason": reason,
            "amount": amount,
            "cumulative": self.total,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        logger.debug("[%s] +%.2f pts (%s) → total=%.2f", self.protocol, amount, reason, self.total)


class PointsTracker:
    """Aggregates points across all integrated protocols."""

    def __init__(self) -> None:
        self.protocols: dict[str, ProtocolPoints] = {
            name: ProtocolPoints(protocol=name)
            for name in PROTOCOL_RATES
        }
        self._days_active: dict[str, int] = {name: 0 for name in PROTOCOL_RATES}

    def record_trade(self, protocol: str) -> None:
        if protocol in self.protocols:
            rate = PROTOCOL_RATES[protocol].get("per_trade", 0.0)
            self.protocols[protocol].add("trade", rate)

    def record_deposit(self, protocol: str, amount_usdc: float = 0.0) -> None:
        if protocol in self.protocols:
            rate = PROTOCOL_RATES[protocol].get("per_deposit", 0.0)
            borrow_rate = PROTOCOL_RATES[protocol].get("per_borrow_usdc", 0.0)
            pts = rate + borrow_rate * amount_usdc
            if pts > 0:
                self.protocols[protocol].add("deposit", pts)

    def record_lp(self, protocol: str) -> None:
        if protocol in self.protocols:
            rate = PROTOCOL_RATES[protocol].get("per_lp_action", 0.0)
            self.protocols[protocol].add("lp", rate)

    def record_stake(self, protocol: str) -> None:
        if protocol in self.protocols:
            rate = PROTOCOL_RATES[protocol].get("per_stake", 0.0)
            self.protocols[protocol].add("stake", rate)

    def tick_daily_points(self) -> list[dict[str, Any]]:
        """Call once per day (or scaled per tick) to accrue daily-active points."""
        events = []
        for name, pp in self.protocols.items():
            rate = PROTOCOL_RATES[name].get("per_day_active", 0.0)
            if rate > 0:
                pp.add("daily_active", rate)
                self._days_active[name] += 1
                events.append({"protocol": name, "points": rate, "total": pp.total})
        return events

    def summary(self) -> list[dict[str, Any]]:
        return [
            {
                "protocol": pp.protocol,
                "total_points": round(pp.total, 2),
                "days_active": self._days_active.get(pp.protocol, 0),
                "recent_events": pp.events[-5:],
            }
            for pp in sorted(self.protocols.values(), key=lambda x: -x.total)
        ]

    @property
    def grand_total(self) -> float:
        return sum(pp.total for pp in self.protocols.values())
