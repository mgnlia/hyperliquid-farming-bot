"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    SIMULATION_MODE: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    AGENT_LOOP_INTERVAL: float = 3.0
    MAX_POSITION_PCT: float = 0.25
    MAX_DRAWDOWN_PCT: float = 0.18
    KELLY_FRACTION: float = 0.45
    INITIAL_PORTFOLIO_VALUE: float = 10000.0

    SSE_HEARTBEAT_SECONDS: float = 1.0
    MAX_EVENTS: int = 300
    MAX_TRADES: int = 300


settings = Settings()
