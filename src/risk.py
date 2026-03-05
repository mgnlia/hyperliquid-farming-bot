"""Risk management — position limits, drawdown protection, exposure tracking."""
import structlog
from dataclasses import dataclass, field
from datetime import datetime, timezone
from src.config import settings

log = structlog.get_logger(__name__)


@dataclass
class RiskState:
    peak_equity: float = 10000.0  # Starting equity baseline
    current_equity: float = 10000.0
    total_exposure_usd: float = 0.0
    positions: dict[str, float] = field(default_factory=dict)  # asset -> usd_value
    blocked: bool = False
    block_reason: str = ""


_state = RiskState()


def update_equity(equity: float):
    """Update current equity and peak."""
    _state.current_equity = equity
    if equity > _state.peak_equity:
        _state.peak_equity = equity
    _check_drawdown()


def _check_drawdown():
    if _state.peak_equity <= 0:
        return
    drawdown = (_state.peak_equity - _state.current_equity) / _state.peak_equity
    if drawdown >= settings.max_drawdown_pct:
        _state.blocked = True
        _state.block_reason = f"Max drawdown reached: {drawdown:.1%} >= {settings.max_drawdown_pct:.1%}"
        log.warning("risk.drawdown_block", drawdown=f"{drawdown:.1%}", reason=_state.block_reason)


def can_trade(asset: str, usd_size: float) -> tuple[bool, str]:
    """Return (allowed, reason). Called before every order."""
    if _state.blocked:
        return False, _state.block_reason

    # Per-position limit
    current_pos = _state.positions.get(asset, 0.0)
    if current_pos + usd_size > settings.max_position_usd:
        return False, f"Position limit: {current_pos + usd_size:.0f} > {settings.max_position_usd:.0f} USD"

    # Total exposure
    if _state.total_exposure_usd + usd_size > settings.max_total_exposure_usd:
        return False, f"Total exposure: {_state.total_exposure_usd + usd_size:.0f} > {settings.max_total_exposure_usd:.0f} USD"

    return True, ""


def record_open(asset: str, usd_size: float):
    _state.positions[asset] = _state.positions.get(asset, 0.0) + usd_size
    _state.total_exposure_usd += usd_size
    log.info("risk.position_open", asset=asset, usd_size=usd_size, total=_state.total_exposure_usd)


def record_close(asset: str, usd_size: float):
    current = _state.positions.get(asset, 0.0)
    _state.positions[asset] = max(0.0, current - usd_size)
    _state.total_exposure_usd = max(0.0, _state.total_exposure_usd - usd_size)
    log.info("risk.position_close", asset=asset, usd_size=usd_size, total=_state.total_exposure_usd)


def get_risk_summary() -> dict:
    drawdown = 0.0
    if _state.peak_equity > 0:
        drawdown = (_state.peak_equity - _state.current_equity) / _state.peak_equity
    return {
        "blocked": _state.blocked,
        "block_reason": _state.block_reason,
        "current_equity": _state.current_equity,
        "peak_equity": _state.peak_equity,
        "drawdown_pct": round(drawdown * 100, 2),
        "total_exposure_usd": round(_state.total_exposure_usd, 2),
        "max_exposure_usd": settings.max_total_exposure_usd,
        "positions": {k: round(v, 2) for k, v in _state.positions.items() if v > 0},
        "max_position_usd": settings.max_position_usd,
        "simulation_mode": settings.simulation_mode,
    }


def reset_block():
    """Manual override to unblock after human review."""
    _state.blocked = False
    _state.block_reason = ""
    log.warning("risk.block_reset_manual")
