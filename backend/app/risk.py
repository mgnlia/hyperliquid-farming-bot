"""Risk management — position limits, drawdown protection."""
import logging
from app.config import settings
from app.database import get_daily_pnl

logger = logging.getLogger(__name__)


async def check_risk() -> dict:
    """Returns {'allowed': bool, 'reason': str}"""
    daily_pnl = await get_daily_pnl()
    if daily_pnl < -settings.daily_loss_limit_usd:
        return {"allowed": False, "reason": f"Daily loss limit hit: ${daily_pnl:.2f} / ${settings.daily_loss_limit_usd:.2f}"}
    return {"allowed": True, "reason": "OK"}


async def position_size(base_usd: float, volatility_factor: float = 1.0) -> float:
    """Adjust position size based on risk params."""
    risk = await check_risk()
    if not risk["allowed"]:
        return 0.0
    adjusted = base_usd / max(volatility_factor, 0.1)
    return min(adjusted, settings.max_position_size_usd)
