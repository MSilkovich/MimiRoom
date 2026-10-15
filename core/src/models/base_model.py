import datetime

from sqlalchemy import TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    __abstract__ = True

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=func.now(),
        onupdate=func.now()
    )
    # Аудит: id пользователя, от чьего имени создана/изменена запись.
    # Заполняется автоматически в репозитории из контекста (см. src/context.py),
    # который выставляется на уровне роутера. Nullable, пока не подключена
    # авторизация; при необходимости можно перевести в NOT NULL.
    who_create: Mapped[int | None] = mapped_column(nullable=True)
    who_update: Mapped[int | None] = mapped_column(nullable=True)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"
