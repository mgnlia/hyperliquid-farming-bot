"""
Equity Perps Trading Strategy — HIP-3 markets via Hyperliquid SDK
Trades perpetual contracts to accumulate trading volume for airdrop points.
"""
import asyncio
import logging
import random
from typing import Optional
from app.config import settings
from app.database import record_trade, get_daily_pnl

logger = logging.getLogger(__name__)

# Top liquid perp markets on Hyperliquid
PERP_MARKETS = ["BTC", "ETH", "SOL", "ARB", "AVAX", "MATIC", "LINK", "DOGE", "WIF", "HYPE"]


class PerpTrader:
    def __init__(self):
        self.running = False
        self.positions: dict = {}
        self.trade_count = 0
        self.total_volume = 0.0
        self._client = None

    def _get_client(self):
        """Lazy init Hyperliquid client (only in live mode)."""
        if settings.simulation_mode:
            return None
        if self._client is None:
            try:
                from hyperliquid.exchange import Exchange
                from eth_account import Account
                account = Account.from_key(settings.private_key)
                self._client = Exchange(account, settings.hl_mainnet_url)
            except Exception as e:
                logger.error(f"Failed to init Hyperliquid client: {e}")
        return self._client

    async def get_market_price(self, symbol: str) -> float:
        """Fetch current mid price for a symbol."""
        if settings.simulation_mode:
            # Simulated prices
            prices = {
                "BTC": 65000 + random.uniform(-500, 500),
                "ETH": 3500 + random.uniform(-50, 50),
                "SOL": 180 + random.uniform(-5, 5),
                "ARB": 1.2 + random.uniform(-0.05, 0.05),
                "AVAX": 35 + random.uniform(-1, 1),
                "MATIC": 0.8 + random.uniform(-0.02, 0.02),
                "LINK": 18 + random.uniform(-0.5, 0.5),
                "DOGE": 0.18 + random.uniform(-0.005, 0.005),
                "WIF": 3.5 + random.uniform(-0.1, 0.1),
                "HYPE": 28 + random.uniform(-1, 1),
            }
            return prices.get(symbol, 100.0)

        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.hl_mainnet_url}/info",
                    json={"type": "allMids"},
                    timeout=10
                )
                data = resp.json()
                return float(data.get(symbol, 0))
        except Exception as e:
            logger.error(f"Price fetch error for {symbol}: {e}")
            return 0.0

    async def place_order(self, symbol: str, side: str, size_usd: float) -> Optional[dict]:
        """Place a perp order (simulated or live)."""
        price = await self.get_market_price(symbol)
        if price <= 0:
            return None

        size_contracts = size_usd / price

        if settings.simulation_mode:
            trade_id = await record_trade(
                strategy="perp_trading",
                symbol=symbol,
                side=side,
                size_usd=size_usd,
                entry_price=price,
                simulated=True
            )
            self.trade_count += 1
            self.total_volume += size_usd
            logger.info(f"[SIM] {side} {symbol} ${size_usd:.2f} @ ${price:.2f} | id={trade_id}")
            return {"id": trade_id, "symbol": symbol, "side": side, "price": price, "size_usd": size_usd}

        # Live order
        client = self._get_client()
        if not client:
            return None
        try:
            is_buy = side == "buy"
            result = client.order(symbol, is_buy, size_contracts, price, {"limit": {"tif": "Gtc"}})
            await record_trade(strategy="perp_trading", symbol=symbol, side=side,
                               size_usd=size_usd, entry_price=price, simulated=False)
            self.trade_count += 1
            self.total_volume += size_usd
            return result
        except Exception as e:
            logger.error(f"Order failed {symbol} {side}: {e}")
            return None

    async def run_volume_farming_cycle(self):
        """Execute a volume farming cycle: buy then sell to generate volume."""
        daily_pnl = await get_daily_pnl()
        if daily_pnl < -settings.daily_loss_limit_usd:
            logger.warning(f"Daily loss limit hit: ${daily_pnl:.2f}. Halting perp trading.")
            return

        symbol = random.choice(PERP_MARKETS)
        size = settings.perp_trade_size_usd

        # Buy
        buy_result = await self.place_order(symbol, "buy", size)
        if buy_result:
            await asyncio.sleep(2)
            # Sell to close (market neutral — just farming volume)
            await self.place_order(symbol, "sell", size)

    async def get_status(self) -> dict:
        return {
            "running": self.running,
            "trade_count": self.trade_count,
            "total_volume_usd": self.total_volume,
            "simulation_mode": settings.simulation_mode,
        }
