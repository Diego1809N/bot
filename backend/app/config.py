from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite:///./scalper.db"

    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_testnet: bool = True

    symbol: str = "BTCUSDT"
    leverage: int = 70
    timeframe: str = "1m"
    mode: Literal["PAPER", "LIVE"] = "PAPER"

    entry_score: int = 5
    cooldown_seconds: int = 0
    max_open_positions: int = 1

    position_usdt: float = 10
    tp_percent: float = 0.20
    sl_percent: float = 0.15
    trailing_enabled: bool = True
    trailing_activation_percent: float = 0.10
    trailing_distance_percent: float = 0.08

    ema_fast: int = 20
    ema_mid: int = 50
    ema_slow: int = 200
    rsi_length: int = 14
    adx_length: int = 14
    momentum_length: int = 5
    volume_length: int = 20

    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


settings = Settings()
