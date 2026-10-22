import datetime

from sqlalchemy import TIMESTAMP, false, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    __abstract__ = True

    is_deleted: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=false(),)

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=func.now(),
        onupdate=func.now()
    )
    # Аудит: id пользователя, от чьего имени создана/изменена запись.
    # Заполняется автоматически в репозитории из контекста (см. src/context.py),
    # который выставляется на уровне роутера.
    who_create: Mapped[int | None] = mapped_column(nullable=False)
    who_update: Mapped[int | None] = mapped_column(nullable=False)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"
