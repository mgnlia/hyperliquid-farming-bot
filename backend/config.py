"""Configuration module using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    SIMULATION_MODE: bool = True
    HYPERLIQUID_RPC_URL: str = "https://api.hyperliquid.xyz"
    HYPERLIQUID_PRIVATE_KEY: str = ""
    HYPERLIQUID_WALLET_ADDRESS: str = ""
    MAX_POSITION_PCT: float = 0.25
    MAX_DRAWDOWN_PCT: float = 0.15
    KELLY_FRACTION: float = 0.5
    AGENT_LOOP_INTERVAL: float = 5.0
    INITIAL_PORTFOLIO_VALUE: float = 10000.0
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    # Auth — Bearer token for non-health endpoints. Empty = auth disabled (dev/CI).
    BOT_API_KEY: str = ""
    # Risk: daily loss cap in USD
    DAILY_LOSS_CAP_USD: float = 500.0
    # Max trades per day before auto-reset at midnight
    MAX_TRADES_PER_DAY: int = 50

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}


settings = Settings()
