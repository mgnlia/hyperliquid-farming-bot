"""Cross-protocol points simulation for airdrop farming."""

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

            base = random.uniform(4, 18)
            bonus = random.uniform(0.9, 1.25)
            earned = base * state.multiplier * bonus

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
        return sum(s.points for s in self.protocols.values())

    def airdrop_score(self) -> float:
        # Heuristic 0-100 score based on total points and coverage
        coverage = sum(1 for s in self.protocols.values() if s.actions_count > 0) / len(self.protocols)
        raw = (self.total_points() / 1500) * 70 + coverage * 30
        return max(0.0, min(100.0, raw))

    def payload(self) -> list[dict]:
        return [
            {
                "protocol": p.protocol,
                "points": round(p.points, 4),
                "multiplier": p.multiplier,
                "actions_count": p.actions_count,
                "last_action": p.last_action,
            }
            for p in self.protocols.values()
        ]
