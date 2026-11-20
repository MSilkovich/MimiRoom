"""Memory stores — хранилища истории диалога.

Доступные реализации:
- ``RedisMemoryStore`` — основная, на Redis List с TTL.
- ``NoopMemoryStore`` — заглушка для тестов / офлайн-режима.
"""

from .base import MemoryStore
from .noop import NoopMemoryStore
from .redis_memory import RedisMemoryStore

__all__ = [
    "MemoryStore",
    "NoopMemoryStore",
    "RedisMemoryStore",
]
