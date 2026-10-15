"""Контекст текущего пользователя для аудита (who_create / who_update).

Значение выставляется на уровне роутера (зависимость ``set_current_user`` из
src/dependencies.py) и читается репозиторием при вставке/обновлении записей.

asyncio выполняет обработку каждого запроса в отдельной task с копией
контекста, поэтому установленное значение изолировано в пределах запроса и не
утекает между запросами.
"""

from contextvars import ContextVar

current_user_id: ContextVar[int | None] = ContextVar("current_user_id", default=None)


def get_current_user_id() -> int | None:
    """Возвращает id пользователя, от чьего имени выполняется операция."""
    return current_user_id.get()


def set_current_user_id(user_id: int | None):
    """Устанавливает id текущего пользователя, возвращает токен для сброса."""
    return current_user_id.set(user_id)
