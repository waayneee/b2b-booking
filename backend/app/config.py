from pydantic_settings import BaseSettings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/booking_db"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = "dev_token"  # Default for development
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    TELEGRAM_MINI_APP_SIGNATURE_SECRET: Optional[str] = None

    # FastAPI
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "Booking Service API"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "change-this-in-production"

    # App settings
    APP_NAME: str = "Booking Bot"
    WEBHOOK_PATH: str = "/webhook"
    APP_DOMAIN: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Log on startup
if settings.TELEGRAM_BOT_TOKEN == "dev_token":
    logger.warning("Using default dev token. Set TELEGRAM_BOT_TOKEN in .env for production.")
if settings.DEBUG:
    logger.warning("DEBUG mode is ON. Use DEBUG=False in production.")
