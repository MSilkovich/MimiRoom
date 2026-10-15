from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.database.db_helper import db_helper
from .context import current_user_id, set_current_user_id
from .repositories.sqlalchemy_uow import SqlAlchemyUnitOfWork
from .repositories.base_uow import UnitOfWork


async def get_session() -> AsyncIterator[AsyncSession]:
    """Отдаёт сессию БД для контроллеров (rollback/close на выходе)."""
    async with db_helper.get_db_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def set_current_user() -> AsyncIterator[int | None]:
    """Пробрасывает id пользователя из авторизации в контекст аудита.

    Подключается в роутере как зависимость (``Depends(set_current_user)``).
    Репозиторий затем подставит это значение в who_create / who_update, т.е.
    будет знать, от чьего имени выполняется изменение. Сейчас авторизация не
    подключена — по умолчанию None ("сейчас забей"). Когда появится токен,
    замените значение на id пользователя, извлечённый из него.
    """
    user_id: int | None = None  # TODO: получать id из токена/заголовка авторизации
    token = set_current_user_id(user_id)
    try:
        yield user_id
    finally:
        current_user_id.reset(token)


CurrentUserDep = Annotated[int | None, Depends(set_current_user)]


def get_uow_factory():
    """Фабрика Unit of Work на базе session_factory приложения.

    FastAPI кэширует результат зависимости в пределах запроса, а каждый
    ``async with uow`` внутри сервиса создаёт собственную транзакцию.
    """

    def uow_factory() -> UnitOfWork:
        return SqlAlchemyUnitOfWork(db_helper.session_factory)

    return uow_factory


UowFactoryDep = Annotated[UnitOfWork, Depends(get_uow_factory)]
