"""
Cross-Protocol Points Tracker
Estimates airdrop score based on trading volume, DeFi activity, and protocol diversity.
"""
import logging
from app.database import get_stats

logger = logging.getLogger(__name__)

# Hyperliquid Season 3 point weights (estimated)
WEIGHTS = {
    "perp_volume": 0.0001,       # points per USD volume
    "defi_volume": 0.0005,       # DeFi gets 5x more weight
    "protocol_diversity": 10.0,  # bonus per unique protocol
    "daily_streak": 5.0,         # daily activity bonus
}


class PointsTracker:
    def __init__(self):
        self.estimated_points = 0.0
        self.airdrop_tier = "Bronze"

    async def calculate_score(self) -> dict:
        stats = await get_stats()

        perp_points = stats["total_volume_usd"] * WEIGHTS["perp_volume"]
        defi_points = stats["farm_volume_usd"] * WEIGHTS["defi_volume"]
        diversity_bonus = stats["farm_events"] * WEIGHTS["protocol_diversity"] * 0.01

        total = perp_points + defi_points + diversity_bonus
        self.estimated_points = total

        # Tier estimation based on Season 1/2 data
        if total >= 100000:
            tier = "Diamond"
        elif total >= 10000:
            tier = "Platinum"
        elif total >= 1000:
            tier = "Gold"
        elif total >= 100:
            tier = "Silver"
        else:
            tier = "Bronze"

        self.airdrop_tier = tier

        # Estimate HYPE allocation (rough estimate based on Season 1 distribution)
        # Season 1: ~31M HYPE distributed to ~94K addresses
        # Average: ~330 HYPE per address, top tier: 10,000+ HYPE
        estimated_hype = total * 0.01  # very rough estimate

        return {
            "perp_points": perp_points,
            "defi_points": defi_points,
            "diversity_bonus": diversity_bonus,
            "total_points": total,
            "tier": tier,
            "estimated_hype": estimated_hype,
            "estimated_usd_value": estimated_hype * 28,  # ~$28/HYPE current price
            "stats": stats,
        }
