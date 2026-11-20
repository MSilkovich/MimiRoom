"""Контекст текущего пользователя для аудита (who_create / who_update).

В контексте хранится объект ``User`` (а не просто ``user_id``). Значение
выставляется зависимостями ``get_current_user`` / ``get_optional_user`` из
src/middleware/auth.py (либо ``system_context`` для служебных операций) и
читается репозиторием при вставке/обновлении записей.

asyncio выполняет обработку каждого запроса в отдельной task с копией
контекста, поэтому установленное значение изолировано в пределах запроса и не
утекает между запросами.
"""

from contextlib import contextmanager
from contextvars import ContextVar, Token

from src.models.user import User

# Идентификатор «системного» пользователя. Реальные пользователи создаются
# автоинкрементом с 1, поэтому 0 безопасно использовать как sentinel.
SYSTEM_USER_ID = 0

# Служебный пользователь: на время операций без аутентифицированного
# пользователя (регистрация, выдача/ротация/отзыв токенов) в контекст кладётся
# он. Благодаря этому в контексте во время любой записи в БД всегда есть
# пользователь (реальный либо системный), а guarded-репозиторий не блокирует
# такие операции. Поля аудита (who_create/who_update) при этом становятся 0.
SYSTEM_USER = User(
    user_id=SYSTEM_USER_ID,
    login="Guest",
    password="",
    name="Guest",
    surname="Guest",
)


def fake_user_factory(id: int) -> User:
    return SYSTEM_USER if id == SYSTEM_USER_ID else User(
        user_id=id,
        login="Anonymous",
        password="",
        name="Anonymous",
        surname="Anonymous",
    )


current_user: ContextVar[User | None] = ContextVar(
    "current_user", default=None)


def get_current_user() -> User | None:
    """Возвращает пользователя, от чьего имени выполняется операция."""
    return current_user.get()


def set_current_user(user: User | None) -> Token:
    """Устанавливает текущего пользователя в контекст."""
    return current_user.set(user)


@contextmanager
def system_context(fake_user_id: int = SYSTEM_USER_ID):
    """Выполнить блок от имени системного пользователя.

    Нужен для служебных операций (регистрация, выдача/ротация/отзыв токенов),
    у которых ещё нет аутентифицированного пользователя, но которые пишут в БД.
    Guarded-репозиторий увидит непустой контекст и не заблокирует запись, но
    поля аудита (who_create/who_update) останутся пустыми.
    """
    token = current_user.set(fake_user_factory(fake_user_id))
    try:
        yield
    finally:
        current_user.reset(token)
