from pathlib import Path

from dotenv import load_dotenv

from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    LOG_LEVEL: str = "DEBUG"

    LOG_CONSOLE: bool = True

    LOG_FILE: bool = False
    LOG_FILE_PATH: Path = Path("logs") / "core.log"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_FILE_BACKUP_COUNT: int = 5


settings_logging = Settings()
