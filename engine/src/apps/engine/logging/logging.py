from logging.config import dictConfig

from config.logging import settings_logging
from config.project_config import settings_app

LOGGER_NAME = settings_app.PROJECT_NAME.lower()


def _build_log_config() -> dict:
    handlers: dict = {}
    active_handlers: list[str] = []

    if settings_logging.LOG_CONSOLE:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        }
        active_handlers.append("console")

    if settings_logging.LOG_FILE:
        log_path = settings_logging.LOG_FILE_PATH
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers["app_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": str(log_path),
            "maxBytes": settings_logging.LOG_FILE_MAX_BYTES,
            "backupCount": settings_logging.LOG_FILE_BACKUP_COUNT,
            "encoding": "utf-8",
        }
        active_handlers.append("app_file")

    if not active_handlers:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stderr",
        }
        active_handlers.append("console")

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            },
        },
        "handlers": handlers,
        "loggers": {
            LOGGER_NAME: {
                "level": settings_logging.LOG_LEVEL,
                "handlers": active_handlers,
                "propagate": False,
            },
        },
        # root не трогаем - uvicorn управляет своим логированием сам
    }


def setup_logging() -> None:
    dictConfig(_build_log_config())
