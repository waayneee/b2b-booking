from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/booking_db"

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    TELEGRAM_MINI_APP_SIGNATURE_SECRET: Optional[str] = None

    # FastAPI
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "Booking Service API"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # App settings
    APP_NAME: str = "Booking Bot"
    WEBHOOK_PATH: str = "/webhook"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
