"""Configuration module using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Mode
    SIMULATION_MODE: bool = True

    # Hyperliquid
    HYPERLIQUID_RPC_URL: str = "https://api.hyperliquid.xyz"
    HYPERLIQUID_PRIVATE_KEY: str = ""
    HYPERLIQUID_WALLET_ADDRESS: str = ""

    # Risk parameters
    MAX_POSITION_PCT: float = 0.25
    MAX_DRAWDOWN_PCT: float = 0.15
    KELLY_FRACTION: float = 0.5

    # Agent
    AGENT_LOOP_INTERVAL: float = 5.0
    INITIAL_PORTFOLIO_VALUE: float = 10000.0

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}


settings = Settings()
