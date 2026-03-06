"""Cross-protocol points farming simulation."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass


@dataclass
class ProtocolPoints:
    protocol: str
    points: float
    multiplier: float
    actions_count: int
    last_action: float


class PointFarmerStrategy:
    def __init__(self):
        now = time.time()
        self.protocols: dict[str, ProtocolPoints] = {
            "Felix": ProtocolPoints("Felix", 0.0, 1.20, 0, now),
            "Mizu": ProtocolPoints("Mizu", 0.0, 1.10, 0, now),
            "Drip": ProtocolPoints("Drip", 0.0, 1.35, 0, now),
            "Hyperbeat": ProtocolPoints("Hyperbeat", 0.0, 1.50, 0, now),
        }

    def farm_cycle(self) -> list[dict]:
        events: list[dict] = []
        now = time.time()

        for name, state in self.protocols.items():
            if random.random() < 0.35:
                continue

            earned = random.uniform(4, 18) * state.multiplier * random.uniform(0.9, 1.25)
            state.points += earned
            state.actions_count += 1
            state.last_action = now
            events.append(
                {
                    "type": "points_farmed",
                    "protocol": name,
                    "earned": round(earned, 4),
                    "total": round(state.points, 4),
                    "timestamp": now,
                }
            )

        return events

    def total_points(self) -> float:
        return sum(state.points for state in self.protocols.values())

    def airdrop_score(self) -> float:
        coverage = sum(1 for state in self.protocols.values() if state.actions_count > 0) / len(self.protocols)
        raw = (self.total_points() / 1500) * 70 + coverage * 30
        return max(0.0, min(100.0, raw))

    def payload(self) -> list[dict]:
        return [
            {
                "protocol": state.protocol,
                "points": round(state.points, 4),
                "multiplier": state.multiplier,
                "actions_count": state.actions_count,
                "last_action": state.last_action,
            }
            for state in self.protocols.values()
        ]
