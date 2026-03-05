"""
HyperEVM DeFi Farming Strategy
Interacts with KittenSwap LP, HypurrFi staking, HyperLend lending
to accumulate DeFi activity points for the Season 3 airdrop.
"""
import asyncio
import logging
import random
from app.config import settings
from app.database import record_farm_event

logger = logging.getLogger(__name__)

# HyperEVM contract addresses (mainnet)
CONTRACTS = {
    "kittenswap_router": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # Uniswap V2 fork
    "hypurrfi_staking": "0x3b02dA8Cb0d097eB8D57A175b88c7D8b47997507",
    "hyperlend_pool": "0x4b02dA8Cb0d097eB8D57A175b88c7D8b47997508",
    "usdc": "0x6d1e7cde53ba9467b783cb7c530ce054",
    "whype": "0x5555555555555555555555555555555555555555",
}

PROTOCOLS = ["KittenSwap", "HypurrFi", "HyperLend", "Felix", "Mizu", "Drip", "Hyperbeat"]


class HyperEVMFarmer:
    def __init__(self):
        self.running = False
        self.farm_count = 0
        self.total_farm_volume = 0.0
        self.protocols_used: set = set()
        self._w3 = None

    def _get_web3(self):
        if settings.simulation_mode:
            return None
        if self._w3 is None:
            try:
                from web3 import Web3
                self._w3 = Web3(Web3.HTTPProvider(settings.hyperevm_rpc))
            except Exception as e:
                logger.error(f"Web3 init failed: {e}")
        return self._w3

    async def simulate_swap(self, protocol: str, amount_usd: float) -> dict:
        """Simulate a swap on a DEX."""
        points = amount_usd * 0.001 * random.uniform(0.8, 1.2)  # ~0.1% of volume as points
        await record_farm_event(
            protocol=protocol,
            action="swap",
            amount_usd=amount_usd,
            points=points,
            simulated=True
        )
        self.farm_count += 1
        self.total_farm_volume += amount_usd
        self.protocols_used.add(protocol)
        logger.info(f"[SIM] Swap on {protocol}: ${amount_usd:.2f} → {points:.4f} pts")
        return {"protocol": protocol, "action": "swap", "amount_usd": amount_usd, "points": points}

    async def simulate_lp(self, protocol: str, amount_usd: float) -> dict:
        """Simulate adding liquidity."""
        points = amount_usd * 0.005 * random.uniform(0.8, 1.2)  # LP earns more points
        await record_farm_event(
            protocol=protocol,
            action="add_liquidity",
            amount_usd=amount_usd,
            points=points,
            simulated=True
        )
        self.farm_count += 1
        self.total_farm_volume += amount_usd
        self.protocols_used.add(protocol)
        logger.info(f"[SIM] LP on {protocol}: ${amount_usd:.2f} → {points:.4f} pts")
        return {"protocol": protocol, "action": "add_liquidity", "amount_usd": amount_usd, "points": points}

    async def simulate_lend(self, protocol: str, amount_usd: float) -> dict:
        """Simulate lending/borrowing."""
        points = amount_usd * 0.003 * random.uniform(0.8, 1.2)
        await record_farm_event(
            protocol=protocol,
            action="lend",
            amount_usd=amount_usd,
            points=points,
            simulated=True
        )
        self.farm_count += 1
        self.total_farm_volume += amount_usd
        self.protocols_used.add(protocol)
        logger.info(f"[SIM] Lend on {protocol}: ${amount_usd:.2f} → {points:.4f} pts")
        return {"protocol": protocol, "action": "lend", "amount_usd": amount_usd, "points": points}

    async def run_farm_cycle(self) -> list:
        """Run one full farming cycle across multiple protocols."""
        results = []

        # KittenSwap LP
        results.append(await self.simulate_swap("KittenSwap", random.uniform(20, 50)))
        await asyncio.sleep(1)

        # HypurrFi staking
        results.append(await self.simulate_lp("HypurrFi", random.uniform(30, 80)))
        await asyncio.sleep(1)

        # HyperLend
        results.append(await self.simulate_lend("HyperLend", random.uniform(25, 60)))
        await asyncio.sleep(1)

        # Cross-protocol points (Felix, Mizu, Drip, Hyperbeat)
        for protocol in ["Felix", "Mizu", "Drip", "Hyperbeat"]:
            results.append(await self.simulate_swap(protocol, random.uniform(10, 30)))
            await asyncio.sleep(0.5)

        return results

    async def get_status(self) -> dict:
        return {
            "running": self.running,
            "farm_count": self.farm_count,
            "total_farm_volume_usd": self.total_farm_volume,
            "protocols_used": list(self.protocols_used),
            "simulation_mode": settings.simulation_mode,
        }
