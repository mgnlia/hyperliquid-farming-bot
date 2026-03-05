"""HyperEVM DeFi farming — KittenSwap LP, HyperLend, HypurrFi staking.

MVP runs in simulation mode — no live transactions.
All contract addresses and APY figures are illustrative.
"""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FarmPosition:
    protocol: str
    type: str           # "lp" | "lend" | "stake"
    amount: float
    apy_est: float      # estimated APY
    points_per_day: float
    opened_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cumulative_points: float = 0.0


class HyperEVMFarmer:
    """Manages DeFi farming positions across HyperEVM protocols."""

    def __init__(self) -> None:
        self.positions: list[FarmPosition] = []
        self._initialized = False

    # ── Open positions ────────────────────────────────────────────────────────

    def _open_kittenswap_lp(self) -> FarmPosition:
        """Simulate adding USDC/HYPE LP on KittenSwap."""
        apy = round(random.uniform(0.15, 0.45), 3)   # 15–45% APY
        pos = FarmPosition(
            protocol="KittenSwap",
            type="lp",
            amount=settings.kittenswap_lp_amount_usdc,
            apy_est=apy,
            points_per_day=8.0,
        )
        logger.info("KittenSwap LP opened: $%.2f @ %.1f%% APY", pos.amount, apy * 100)
        return pos

    def _open_hyperlend(self) -> FarmPosition:
        """Simulate depositing USDC into HyperLend."""
        apy = round(random.uniform(0.06, 0.18), 3)   # 6–18% APY
        pos = FarmPosition(
            protocol="HyperLend",
            type="lend",
            amount=settings.hyperlend_deposit_usdc,
            apy_est=apy,
            points_per_day=5.0,
        )
        logger.info("HyperLend deposit: $%.2f @ %.1f%% APY", pos.amount, apy * 100)
        return pos

    def _open_hypurrfi(self) -> FarmPosition:
        """Simulate staking HYPE on HypurrFi."""
        apy = round(random.uniform(0.08, 0.20), 3)   # 8–20% APY
        pos = FarmPosition(
            protocol="HypurrFi",
            type="stake",
            amount=settings.hypurrfi_stake_hype,
            apy_est=apy,
            points_per_day=6.0,
        )
        logger.info("HypurrFi stake: %.2f HYPE @ %.1f%% APY", pos.amount, apy * 100)
        return pos

    # ── Tick ─────────────────────────────────────────────────────────────────

    async def tick(self) -> list[dict[str, Any]]:
        """Open positions on first tick; accrue points every tick."""
        events: list[dict[str, Any]] = []

        if not self._initialized:
            self.positions = [
                self._open_kittenswap_lp(),
                self._open_hyperlend(),
                self._open_hypurrfi(),
            ]
            self._initialized = True
            events.append({"event": "positions_opened", "count": len(self.positions)})

        # Accrue simulated points (1 tick ≈ 1 minute → scale to day fraction)
        tick_fraction = settings.loop_interval_seconds / 86400.0
        for pos in self.positions:
            earned = pos.points_per_day * tick_fraction
            pos.cumulative_points += earned
            events.append({
                "event": "points_accrued",
                "protocol": pos.protocol,
                "earned": round(earned, 6),
                "cumulative": round(pos.cumulative_points, 4),
            })

        return events

    def status(self) -> dict[str, Any]:
        return {
            "strategy": "hyper_evm_farming",
            "positions": [
                {
                    "protocol": p.protocol,
                    "type": p.type,
                    "amount": p.amount,
                    "apy_est": p.apy_est,
                    "points_per_day": p.points_per_day,
                    "cumulative_points": round(p.cumulative_points, 4),
                    "opened_at": p.opened_at,
                }
                for p in self.positions
            ],
            "total_tvl": sum(p.amount for p in self.positions),
            "total_points": round(sum(p.cumulative_points for p in self.positions), 4),
        }
