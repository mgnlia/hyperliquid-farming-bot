"""DeFi farming strategy: KittenSwap LP, HypurrFi staking, HyperLend lending."""

import random
import time
from dataclasses import dataclass, field


@dataclass
class DeFiPosition:
    """Represents a DeFi farming position."""

    protocol: str
    pool: str
    deposited: float
    apy: float
    earned: float = 0.0
    started_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "protocol": self.protocol,
            "pool": self.pool,
            "deposited": round(self.deposited, 2),
            "apy": round(self.apy, 4),
            "earned": round(self.earned, 2),
            "started_at": self.started_at,
        }


DEFI_POOLS = [
    {"protocol": "KittenSwap", "pool": "HYPE/USDC LP", "base_apy": 0.45, "apy_vol": 0.1},
    {"protocol": "KittenSwap", "pool": "ETH/HYPE LP", "base_apy": 0.38, "apy_vol": 0.08},
    {"protocol": "HypurrFi", "pool": "HYPE Staking", "base_apy": 0.22, "apy_vol": 0.05},
    {"protocol": "HypurrFi", "pool": "PURR/HYPE Vault", "base_apy": 0.55, "apy_vol": 0.15},
    {"protocol": "HyperLend", "pool": "USDC Lending", "base_apy": 0.12, "apy_vol": 0.03},
    {"protocol": "HyperLend", "pool": "ETH Lending", "base_apy": 0.08, "apy_vol": 0.02},
    {"protocol": "HyperLend", "pool": "HYPE Lending", "base_apy": 0.18, "apy_vol": 0.06},
]


class DeFiFarmingStrategy:
    """Simulated DeFi farming across HyperEVM protocols."""

    def __init__(self):
        self.positions: list[DeFiPosition] = []
        self.total_earned: float = 0.0
        self.events: list[dict] = []

    def _get_current_apy(self, pool_config: dict) -> float:
        base = pool_config["base_apy"]
        vol = pool_config["apy_vol"]
        return max(0.01, base + random.gauss(0, vol))

    def execute(self, available_capital: float) -> list[dict]:
        """Run DeFi farming: accrue yields, rebalance positions."""
        events = []

        for pos in self.positions:
            time_elapsed = 5.0 / (365 * 24 * 3600)
            yield_earned = pos.deposited * pos.apy * time_elapsed
            pos.earned += yield_earned
            self.total_earned += yield_earned
            for pool_cfg in DEFI_POOLS:
                if pool_cfg["protocol"] == pos.protocol and pool_cfg["pool"] == pos.pool:
                    pos.apy = self._get_current_apy(pool_cfg)
                    break

        if len(self.positions) < 4 and available_capital > 100:
            pool_cfg = random.choice(DEFI_POOLS)
            existing = [p for p in self.positions if p.protocol == pool_cfg["protocol"] and p.pool == pool_cfg["pool"]]
            if not existing:
                deposit_amount = min(available_capital * random.uniform(0.15, 0.35), available_capital)
                apy = self._get_current_apy(pool_cfg)
                pos = DeFiPosition(protocol=pool_cfg["protocol"], pool=pool_cfg["pool"], deposited=deposit_amount, apy=apy)
                self.positions.append(pos)
                event = {
                    "type": "defi_deposit",
                    "protocol": pos.protocol,
                    "pool": pos.pool,
                    "amount": round(deposit_amount, 2),
                    "apy": round(apy, 4),
                    "timestamp": time.time(),
                }
                events.append(event)
                self.events.append(event)

        if random.random() < 0.05 and self.positions:
            worst = min(self.positions, key=lambda p: p.apy)
            if worst.apy < 0.05:
                event = {
                    "type": "defi_withdraw",
                    "protocol": worst.protocol,
                    "pool": worst.pool,
                    "amount": round(worst.deposited + worst.earned, 2),
                    "earned": round(worst.earned, 2),
                    "timestamp": time.time(),
                }
                events.append(event)
                self.events.append(event)
                self.positions.remove(worst)

        return events

    def get_positions(self) -> list[dict]:
        return [p.to_dict() for p in self.positions]

    def get_total_deposited(self) -> float:
        return sum(p.deposited for p in self.positions)

    def get_total_earned(self) -> float:
        return self.total_earned
