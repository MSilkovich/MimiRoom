import logging
from config.project_config import settings_app


def get_logger(name: str | None = None) -> logging.Logger:
    base = settings_app.PROJECT_NAME.lower()
    return logging.getLogger(f"{base}.{name}" if name else base)
