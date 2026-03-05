"""
Perps strategy — equity perpetuals trading via Hyperliquid SDK.
SIMULATION_MODE=true by default (no real orders placed).
Earns trading volume for airdrop points.
"""
import asyncio
import random
import structlog
from datetime import datetime, timezone
from src.config import settings
from src import risk, database

log = structlog.get_logger(__name__)

# Strategy state
_state = {
    "running": False,
    "total_trades": 0,
    "total_volume_usd": 0.0,
    "open_positions": {},  # coin -> {side, size, entry_price}
    "last_prices": {},     # coin -> price
    "errors": 0,
}


async def _fetch_prices_simulated() -> dict[str, float]:
    """Simulated price feed — replace with real SDK call in live mode."""
    base_prices = {
        "BTC": 65000.0, "ETH": 3500.0, "SOL": 180.0,
        "ARB": 1.20, "AVAX": 38.0, "HYPE": 12.0,
    }
    return {
        coin: price * (1 + random.uniform(-0.005, 0.005))
        for coin, price in base_prices.items()
        if coin in settings.perps_coins
    }


async def _fetch_prices_live() -> dict[str, float]:
    """Real price fetch via Hyperliquid REST API."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{settings.hl_api_url}/info",
                json={"type": "allMids"},
            )
            data = resp.json()
            return {
                coin: float(data.get(coin, 0))
                for coin in settings.perps_coins
                if data.get(coin)
            }
    except Exception as e:
        log.error("perps.price_fetch_error", error=str(e))
        return await _fetch_prices_simulated()


async def fetch_prices() -> dict[str, float]:
    if settings.simulation_mode:
        return await _fetch_prices_simulated()
    return await _fetch_prices_live()


def _decide_side(coin: str, prices: dict[str, float]) -> str:
    """Simple momentum signal — alternates for airdrop volume generation."""
    prev = _state["last_prices"].get(coin, prices[coin])
    return "BUY" if prices[coin] >= prev else "SELL"


async def _place_order_simulated(coin: str, side: str, size: float, price: float) -> str:
    """Simulated order — logs and returns fake tx hash."""
    await asyncio.sleep(0.05)  # Simulate network latency
    fake_hash = f"0xSIM{''.join(random.choices('0123456789abcdef', k=40))}"
    log.info("perps.sim_order", coin=coin, side=side, size=size, price=price, hash=fake_hash)
    return fake_hash


async def _place_order_live(coin: str, side: str, size: float, price: float) -> str:
    """Live order via Hyperliquid SDK."""
    try:
        from hyperliquid.exchange import Exchange
        from eth_account import Account
        account = Account.from_key(settings.private_key)
        exchange = Exchange(account, base_url=settings.hl_api_url)
        is_buy = side == "BUY"
        result = exchange.order(coin, is_buy, size, price, {"limit": {"tif": "Gtc"}})
        if result.get("status") == "ok":
            return result.get("response", {}).get("data", {}).get("statuses", [{}])[0].get("resting", {}).get("oid", "live")
        log.warning("perps.order_rejected", result=result)
        return ""
    except Exception as e:
        log.error("perps.live_order_error", error=str(e))
        return ""


async def run_cycle():
    """Single trading cycle across all configured coins."""
    prices = await fetch_prices()
    _state["last_prices"].update(prices)

    for coin in settings.perps_coins:
        price = prices.get(coin)
        if not price:
            continue

        size_usd = settings.perps_trade_size_usd
        size_coin = round(size_usd / price, 6)
        side = _decide_side(coin, prices)

        allowed, reason = risk.can_trade(coin, size_usd)
        if not allowed:
            log.debug("perps.risk_blocked", coin=coin, reason=reason)
            continue

        if settings.simulation_mode:
            tx = await _place_order_simulated(coin, side, size_coin, price)
        else:
            tx = await _place_order_live(coin, side, size_coin, price)

        if tx:
            risk.record_open(coin, size_usd)
            trade_id = await database.log_trade(
                strategy="perps",
                coin=coin,
                side=side,
                size=size_coin,
                price=price,
                usd_value=size_usd,
                tx_hash=tx,
                simulated=settings.simulation_mode,
            )
            _state["total_trades"] += 1
            _state["total_volume_usd"] += size_usd

            # Auto-close after recording (simple in/out for volume farming)
            await asyncio.sleep(0.1)
            risk.record_close(coin, size_usd)

    _state["last_prices"] = prices
    log.info("perps.cycle_done", trades=_state["total_trades"], volume=f"${_state['total_volume_usd']:.2f}")


async def run(stop_event: asyncio.Event):
    """Main loop — runs every PERPS_INTERVAL_SECONDS."""
    _state["running"] = True
    log.info("perps.start", simulation=settings.simulation_mode, coins=settings.perps_coins)
    try:
        while not stop_event.is_set():
            try:
                await run_cycle()
            except Exception as e:
                _state["errors"] += 1
                log.error("perps.cycle_error", error=str(e))
            await asyncio.sleep(settings.perps_interval_seconds)
    finally:
        _state["running"] = False
        log.info("perps.stopped")


def get_status() -> dict:
    return {
        "strategy": "perps",
        "running": _state["running"],
        "simulation_mode": settings.simulation_mode,
        "total_trades": _state["total_trades"],
        "total_volume_usd": round(_state["total_volume_usd"], 2),
        "coins": settings.perps_coins,
        "trade_size_usd": settings.perps_trade_size_usd,
        "errors": _state["errors"],
    }
