"""
Cross-protocol point farming — Felix, Mizu, Drip, Hyperbeat.
Tracks points from all integrated protocols for $HYPE airdrop optimization.
"""
import asyncio
import random
import structlog
from datetime import datetime, timezone
from src.config import settings
from src import database

log = structlog.get_logger(__name__)

PROTOCOLS = {
    "felix": {
        "name": "Felix Protocol",
        "description": "CDP stablecoin — mint feUSD against HYPE collateral",
        "category": "cdp",
        "actions": ["mint_feusd", "provide_liquidity"],
        "base_points_per_usd_per_day": 1.5,
        "multiplier": 2.0,
        "url": "https://felix.hyperliquid.xyz",
    },
    "mizu": {
        "name": "Mizu Finance",
        "description": "Liquid staking — stake HYPE for mHYPE",
        "category": "liquid_staking",
        "actions": ["stake_hype", "provide_lp"],
        "base_points_per_usd_per_day": 1.2,
        "multiplier": 1.8,
        "url": "https://mizu.finance",
    },
    "drip": {
        "name": "Drip Network",
        "description": "Yield aggregator — auto-compound DeFi positions",
        "category": "yield_aggregator",
        "actions": ["deposit", "autocompound"],
        "base_points_per_usd_per_day": 0.8,
        "multiplier": 1.5,
        "url": "https://drip.hyperliquid.xyz",
    },
    "hyperbeat": {
        "name": "Hyperbeat",
        "description": "Structured products — vaults with boosted yields",
        "category": "structured_products",
        "actions": ["deposit_vault", "claim_rewards"],
        "base_points_per_usd_per_day": 1.0,
        "multiplier": 1.6,
        "url": "https://hyperbeat.xyz",
    },
    "hyperliquid_native": {
        "name": "Hyperliquid DEX",
        "description": "Native perps + spot trading volume",
        "category": "native",
        "actions": ["trade_perps", "trade_spot"],
        "base_points_per_usd_per_day": 0.5,
        "multiplier": 3.0,  # Highest multiplier — native protocol
        "url": "https://app.hyperliquid.xyz",
    },
}

_state = {
    "running": False,
    "points": {p: 0.0 for p in PROTOCOLS},
    "actions_taken": {p: [] for p in PROTOCOLS},
    "total_points": 0.0,
    "estimated_rank": 0,
    "checks": 0,
    "errors": 0,
}


async def _sim_fetch_points(protocol: str) -> float:
    """Simulate point accumulation based on time and activity."""
    base = PROTOCOLS[protocol]["base_points_per_usd_per_day"]
    mult = PROTOCOLS[protocol]["multiplier"]
    # Simulate ~$500 USD position value per protocol
    position_usd = 500.0
    hours_elapsed = settings.points_check_interval_seconds / 3600
    points_gained = base * mult * position_usd * (hours_elapsed / 24)
    noise = random.uniform(0.9, 1.1)
    return round(points_gained * noise, 4)


async def _live_fetch_points(protocol: str) -> float:
    """Real point fetch — protocol-specific API calls."""
    import httpx
    endpoints = {
        "felix": "https://api.felix.hyperliquid.xyz/points",
        "mizu": "https://api.mizu.finance/points",
        "drip": "https://api.drip.hyperliquid.xyz/points",
        "hyperbeat": "https://api.hyperbeat.xyz/points",
        "hyperliquid_native": f"{settings.hl_api_url}/info",
    }
    url = endpoints.get(protocol)
    if not url or not settings.wallet_address:
        return 0.0
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params={"address": settings.wallet_address})
            data = resp.json()
            return float(data.get("points", 0))
    except Exception as e:
        log.error("points.fetch_error", protocol=protocol, error=str(e))
        return 0.0


async def _perform_action(protocol: str, action: str):
    """Simulate or execute a point-earning action."""
    if settings.simulation_mode:
        await asyncio.sleep(0.05)
        log.info("points.sim_action", protocol=protocol, action=action)
        _state["actions_taken"][protocol].append({
            "action": action,
            "at": datetime.now(timezone.utc).isoformat(),
            "simulated": True,
        })
        # Keep only last 10 actions per protocol
        _state["actions_taken"][protocol] = _state["actions_taken"][protocol][-10:]
    else:
        log.warning("points.live_action_not_implemented", protocol=protocol, action=action)


async def run_cycle():
    """Check and accumulate points across all protocols."""
    total = 0.0
    for protocol, meta in PROTOCOLS.items():
        if settings.simulation_mode:
            new_points = await _sim_fetch_points(protocol)
        else:
            new_points = await _live_fetch_points(protocol)

        _state["points"][protocol] += new_points
        total += _state["points"][protocol]

        # Perform a farming action each cycle
        if meta["actions"]:
            action = random.choice(meta["actions"])
            await _perform_action(protocol, action)

        # Log to DB periodically
        await database.upsert_points(protocol, _state["points"][protocol])

    _state["total_points"] = round(total, 4)
    # Estimate rank (very rough simulation)
    _state["estimated_rank"] = max(1, int(10000 / (1 + _state["total_points"] / 1000)))
    _state["checks"] += 1

    log.info(
        "points.cycle_done",
        total_points=_state["total_points"],
        estimated_rank=_state["estimated_rank"],
        protocols=len(PROTOCOLS),
    )


async def run(stop_event: asyncio.Event):
    _state["running"] = True
    log.info("points.start", simulation=settings.simulation_mode, protocols=list(PROTOCOLS.keys()))
    try:
        while not stop_event.is_set():
            try:
                await run_cycle()
            except Exception as e:
                _state["errors"] += 1
                log.error("points.cycle_error", error=str(e))
            await asyncio.sleep(settings.points_check_interval_seconds)
    finally:
        _state["running"] = False
        log.info("points.stopped")


def get_status() -> dict:
    return {
        "strategy": "point_farmer",
        "running": _state["running"],
        "simulation_mode": settings.simulation_mode,
        "total_points": _state["total_points"],
        "estimated_rank": _state["estimated_rank"],
        "checks": _state["checks"],
        "protocols": {
            p: {
                "name": PROTOCOLS[p]["name"],
                "category": PROTOCOLS[p]["category"],
                "points": round(_state["points"][p], 4),
                "multiplier": PROTOCOLS[p]["multiplier"],
                "recent_actions": len(_state["actions_taken"][p]),
            }
            for p in PROTOCOLS
        },
        "errors": _state["errors"],
    }
