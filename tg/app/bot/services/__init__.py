"""Сервисный слой TG-бота: Redis, core-клиент, привязки, стримы."""

from .redis_client import close_redis, ensure_response_group, get_redis
from .core_client import CoreClient, CoreError, CoreNotFound
from .link_cache import remember_link, resolve_user_id
from .task_publisher import publish_incoming
from .response_consumer import run_response_consumer

__all__ = [
    "get_redis",
    "close_redis",
    "ensure_response_group",
    "CoreClient",
    "CoreError",
    "CoreNotFound",
    "remember_link",
    "resolve_user_id",
    "publish_incoming",
    "run_response_consumer",
]
