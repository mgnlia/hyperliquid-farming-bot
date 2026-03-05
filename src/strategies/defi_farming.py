"""
DeFi farming strategy — KittenSwap LP, HypurrFi staking, HyperLend lending.
All on-chain interactions are simulated unless SIMULATION_MODE=false.
"""
import asyncio
import random
import structlog
from datetime import datetime, timezone
from src.config import settings
from src import risk, database

log = structlog.get_logger(__name__)

# Simulated APY data for each protocol
PROTOCOL_META = {
    "kittenswap": {
        "name": "KittenSwap LP",
        "type": "lp",
        "pairs": ["HYPE/USDC", "ETH/USDC", "BTC/USDC"],
        "base_apy": 0.35,   # 35% APY
        "points_multiplier": 2.0,
    },
    "hypurrfi": {
        "name": "HypurrFi Staking",
        "type": "stake",
        "assets": ["HYPE"],
        "base_apy": 0.18,   # 18% APY
        "points_multiplier": 1.5,
    },
    "hyperlend": {
        "name": "HyperLend Lending",
        "type": "lend",
        "assets": ["USDC", "ETH", "BTC"],
        "base_apy": 0.08,   # 8% APY
        "points_multiplier": 1.0,
    },
}

_state = {
    "running": False,
    "positions": {},   # protocol -> {asset, size_usd, apy, entered_at}
    "total_yield_usd": 0.0,
    "rebalances": 0,
    "errors": 0,
}


async def _sim_deposit(protocol: str, asset: str, amount_usd: float) -> str:
    await asyncio.sleep(0.1)
    tx = f"0xDEFI{''.join(random.choices('0123456789abcdef', k=40))}"
    log.info("defi.sim_deposit", protocol=protocol, asset=asset, amount_usd=amount_usd, tx=tx)
    return tx


async def _live_deposit(protocol: str, asset: str, amount_usd: float) -> str:
    """Placeholder for real on-chain deposit via web3.py / HyperEVM."""
    log.warning("defi.live_not_implemented", protocol=protocol)
    return ""


async def _sim_withdraw(protocol: str, asset: str) -> float:
    await asyncio.sleep(0.1)
    pos = _state["positions"].get(protocol, {})
    yield_earned = pos.get("size_usd", 0) * pos.get("apy", 0) / 365
    log.info("defi.sim_withdraw", protocol=protocol, asset=asset, yield_usd=yield_earned)
    return yield_earned


async def _enter_position(protocol: str):
    """Enter a DeFi position for the given protocol."""
    meta = PROTOCOL_META[protocol]
    allowed, reason = risk.can_trade(protocol, settings.perps_trade_size_usd)
    if not allowed:
        log.debug("defi.risk_blocked", protocol=protocol, reason=reason)
        return

    if protocol in _state["positions"]:
        return  # Already in position

    asset = (meta.get("pairs") or meta.get("assets") or ["USDC"])[0]
    amount_usd = settings.perps_trade_size_usd * 2  # DeFi positions are larger

    if settings.simulation_mode:
        tx = await _sim_deposit(protocol, asset, amount_usd)
    else:
        tx = await _live_deposit(protocol, asset, amount_usd)

    if tx:
        risk.record_open(protocol, amount_usd)
        _state["positions"][protocol] = {
            "asset": asset,
            "size_usd": amount_usd,
            "apy": meta["base_apy"],
            "points_multiplier": meta["points_multiplier"],
            "entered_at": datetime.now(timezone.utc).isoformat(),
            "tx": tx,
        }
        await database.log_trade(
            strategy="defi_farming",
            coin=f"{protocol}:{asset}",
            side="DEPOSIT",
            size=amount_usd,
            price=1.0,
            usd_value=amount_usd,
            tx_hash=tx,
            simulated=settings.simulation_mode,
        )


async def _harvest_yield():
    """Harvest simulated yield from all active positions."""
    for protocol, pos in _state["positions"].items():
        # Daily yield accrual (called every rebalance interval)
        hours_held = settings.defi_rebalance_interval_seconds / 3600
        yield_usd = pos["size_usd"] * pos["apy"] * (hours_held / 8760)
        _state["total_yield_usd"] += yield_usd
        log.info("defi.yield_harvest", protocol=protocol, yield_usd=f"${yield_usd:.4f}")


async def run_cycle():
    """Enter all DeFi positions and harvest yield."""
    for protocol in PROTOCOL_META:
        await _enter_position(protocol)

    await _harvest_yield()
    _state["rebalances"] += 1
    log.info("defi.cycle_done", positions=len(_state["positions"]), total_yield=f"${_state['total_yield_usd']:.4f}")


async def run(stop_event: asyncio.Event):
    _state["running"] = True
    log.info("defi.start", simulation=settings.simulation_mode, protocols=list(PROTOCOL_META.keys()))
    try:
        while not stop_event.is_set():
            try:
                await run_cycle()
            except Exception as e:
                _state["errors"] += 1
                log.error("defi.cycle_error", error=str(e))
            await asyncio.sleep(settings.defi_rebalance_interval_seconds)
    finally:
        _state["running"] = False
        log.info("defi.stopped")


def get_status() -> dict:
    return {
        "strategy": "defi_farming",
        "running": _state["running"],
        "simulation_mode": settings.simulation_mode,
        "protocols": list(PROTOCOL_META.keys()),
        "active_positions": len(_state["positions"]),
        "total_yield_usd": round(_state["total_yield_usd"], 4),
        "rebalances": _state["rebalances"],
        "positions": {
            k: {
                "asset": v["asset"],
                "size_usd": v["size_usd"],
                "apy_pct": round(v["apy"] * 100, 1),
                "entered_at": v["entered_at"],
            }
            for k, v in _state["positions"].items()
        },
        "errors": _state["errors"],
    }
