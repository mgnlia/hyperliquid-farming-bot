from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Mode
    simulation_mode: bool = True

    # Wallet
    private_key: Optional[str] = None
    wallet_address: Optional[str] = None

    # Hyperliquid
    hl_mainnet_url: str = "https://api.hyperliquid.xyz"
    hl_testnet_url: str = "https://api.hyperliquid-testnet.xyz"
    use_testnet: bool = False

    # HyperEVM
    hyperevm_rpc: str = "https://rpc.hyperliquid.xyz/evm"

    # Strategy params
    perp_trade_size_usd: float = 50.0
    max_position_size_usd: float = 500.0
    daily_loss_limit_usd: float = 100.0
    farm_trade_interval_secs: int = 3600  # 1 hour

    # API security
    bot_api_key: str = "changeme-set-BOT_API_KEY-env"

    # Database
    db_path: str = "data/hyperliquid.db"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
