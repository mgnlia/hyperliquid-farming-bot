"""Configuration — all settings loaded from env vars or .env file."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── General ────────────────────────────────────────────────────────────────
    simulation_mode: bool = True
    bot_name: str = "HyperFarmer-v1"
    loop_interval_seconds: int = 60

    # ── Hyperliquid API ────────────────────────────────────────────────────────
    hl_api_url: str = "https://api.hyperliquid.xyz"
    hl_wallet_address: str = ""
    hl_private_key: str = ""

    # ── HyperEVM ───────────────────────────────────────────────────────────────
    hyper_evm_rpc: str = "https://rpc.hyperliquid.xyz/evm"
    hyper_evm_chain_id: int = 999

    # ── Strategy limits ────────────────────────────────────────────────────────
    max_position_usdc: float = 100.0
    daily_perp_trades: int = 5
    max_drawdown_pct: float = 0.15
    perp_trade_size_usdc: float = 10.0

    # ── KittenSwap ─────────────────────────────────────────────────────────────
    kittenswap_router: str = "0x0000000000000000000000000000000000000000"
    kittenswap_lp_amount_usdc: float = 20.0

    # ── HyperLend ──────────────────────────────────────────────────────────────
    hyperlend_pool: str = "0x0000000000000000000000000000000000000000"
    hyperlend_deposit_usdc: float = 25.0

    # ── HypurrFi ───────────────────────────────────────────────────────────────
    hypurrfi_staking: str = "0x0000000000000000000000000000000000000000"
    hypurrfi_stake_hype: float = 5.0

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
