"""Simulated HyperEVM DeFi farming actions."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass


@dataclass
class DefiPosition:
    protocol: str
    pool: str
    deposited: float
    apy: float
    started_at: float
    earned: float = 0.0


class DefiFarmingStrategy:
    def __init__(self):
        self.positions: list[DefiPosition] = [
            DefiPosition("KittenSwap", "USDC-HYPE LP", 1500.0, 0.35, time.time()),
            DefiPosition("HypurrFi", "HYPE Staking", 1200.0, 0.22, time.time()),
            DefiPosition("HyperLend", "USDC Lending", 1700.0, 0.18, time.time()),
        ]

    def accrue_yield(self, seconds: float) -> float:
        total = 0.0
        for position in self.positions:
            per_second_rate = position.apy / (365 * 24 * 3600)
            base_yield = position.deposited * per_second_rate * seconds
            delta = base_yield * random.uniform(0.95, 1.05)
            position.earned += delta
            total += delta
        return total

    def rebalance(self) -> dict | None:
        if random.random() < 0.7:
            return None

        position = random.choice(self.positions)
        shift = random.uniform(-0.08, 0.12)
        amount = max(10.0, position.deposited * abs(shift))

        if shift > 0:
            position.deposited += amount
            action = "deposit"
        else:
            position.deposited = max(200.0, position.deposited - amount)
            action = "withdraw"

        return {
            "type": "defi_rebalance",
            "protocol": position.protocol,
            "pool": position.pool,
            "action": action,
            "amount": round(amount, 4),
            "timestamp": time.time(),
        }

    def total_earned(self) -> float:
        return sum(position.earned for position in self.positions)

    def total_deposited(self) -> float:
        return sum(position.deposited for position in self.positions)

    def positions_payload(self) -> list[dict]:
        return [
            {
                "protocol": position.protocol,
                "pool": position.pool,
                "deposited": round(position.deposited, 4),
                "apy": round(position.apy, 4),
                "earned": round(position.earned, 4),
                "started_at": position.started_at,
            }
            for position in self.positions
        ]
