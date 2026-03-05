"""Cross-protocol point accumulation strategy for airdrop farming."""

import random
import time
from dataclasses import dataclass, field


@dataclass
class ProtocolPoints:
    """Tracks points for a specific protocol."""

    protocol: str
    points: float = 0.0
    multiplier: float = 1.0
    actions_count: int = 0
    last_action: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "protocol": self.protocol,
            "points": round(self.points, 2),
            "multiplier": round(self.multiplier, 2),
            "actions_count": self.actions_count,
            "last_action": self.last_action,
        }


PROTOCOL_CONFIGS = [
    {"name": "Felix", "base_points": 15.0, "actions": ["mint_stablecoin", "provide_collateral", "borrow", "repay"], "mult_range": (1.0, 2.5)},
    {"name": "Mizu", "base_points": 12.0, "actions": ["deposit_vault", "stake_lp", "claim_rewards"], "mult_range": (1.0, 3.0)},
    {"name": "Drip", "base_points": 20.0, "actions": ["daily_check_in", "swap", "provide_liquidity", "refer_user"], "mult_range": (1.0, 2.0)},
    {"name": "Hyperbeat", "base_points": 10.0, "actions": ["stake_hype", "vote_governance", "delegate"], "mult_range": (1.0, 4.0)},
    {"name": "HyperLend", "base_points": 8.0, "actions": ["supply_asset", "borrow_asset", "repay_loan"], "mult_range": (1.0, 2.0)},
    {"name": "KittenSwap", "base_points": 18.0, "actions": ["swap_tokens", "add_liquidity", "farm_rewards"], "mult_range": (1.0, 2.5)},
]


class PointFarmerStrategy:
    """Simulated cross-protocol point accumulation."""

    def __init__(self):
        self.protocol_points: dict[str, ProtocolPoints] = {}
        self.events: list[dict] = []
        self._init_protocols()

    def _init_protocols(self):
        for cfg in PROTOCOL_CONFIGS:
            self.protocol_points[cfg["name"]] = ProtocolPoints(
                protocol=cfg["name"],
                multiplier=random.uniform(*cfg["mult_range"]),
            )

    def execute(self) -> list[dict]:
        """Execute point farming actions across protocols."""
        events = []
        num_actions = random.randint(1, 3)
        for _ in range(num_actions):
            cfg = random.choice(PROTOCOL_CONFIGS)
            action = random.choice(cfg["actions"])
            pp = self.protocol_points[cfg["name"]]

            if random.random() < 0.1:
                pp.multiplier = random.uniform(*cfg["mult_range"])

            points_earned = cfg["base_points"] * pp.multiplier * random.uniform(0.8, 1.5)
            pp.points += points_earned
            pp.actions_count += 1
            pp.last_action = time.time()

            event = {
                "type": "points_earned",
                "protocol": cfg["name"],
                "action": action,
                "points": round(points_earned, 2),
                "total_points": round(pp.points, 2),
                "multiplier": round(pp.multiplier, 2),
                "timestamp": time.time(),
            }
            events.append(event)
            self.events.append(event)

        return events

    def get_points_breakdown(self) -> list[dict]:
        return [pp.to_dict() for pp in self.protocol_points.values()]

    def get_total_points(self) -> float:
        return sum(pp.points for pp in self.protocol_points.values())

    def get_airdrop_score(self) -> float:
        """Calculate composite airdrop score (0-100)."""
        total = self.get_total_points()
        protocols_active = sum(1 for pp in self.protocol_points.values() if pp.actions_count > 0)
        diversity_bonus = protocols_active * 5
        score = min(100, (total / 50) + diversity_bonus)
        return round(score, 2)
