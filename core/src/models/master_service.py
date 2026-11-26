from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .service import Service
    from .user import User


class MasterService(Base):
    """Связь мастер (user) - услуга.

    Мастер — это ``user`` с ролью ``groomer``; отдельного признака/таблицы
    ресурсов нет.
    """

    __tablename__ = "master_services"

    master_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("service.service_id", ondelete="CASCADE"),
        primary_key=True,
    )

    master: Mapped["User"] = relationship(
        "User", lazy="selectin", overlaps="services,masters"
    )
    service: Mapped["Service"] = relationship(
        "Service", lazy="selectin", overlaps="services,masters"
    )
