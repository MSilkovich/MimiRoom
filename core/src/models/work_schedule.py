from datetime import time as time_type
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Time,
    UniqueConstraint,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .resource import Resource


class WorkSchedule(Base):
    """Базовый график работы мастера по дням недели.

    ``weekday`` следует конвенции Python ``date.weekday()``: 0 — понедельник,
    6 — воскресенье. Один интервал на день; ``is_day_off`` помечает выходной.
    """

    __tablename__ = "work_schedules"

    work_schedule_id: Mapped[int] = mapped_column(primary_key=True)
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("resources.resource_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weekday: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[time_type] = mapped_column(Time, nullable=False)
    end_time: Mapped[time_type] = mapped_column(Time, nullable=False)
    is_day_off: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )

    resource: Mapped["Resource"] = relationship(
        "Resource", back_populates="work_schedules", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint(
            "resource_id", "weekday", name="uq_work_schedules_resource_weekday"
        ),
        CheckConstraint(
            "weekday >= 0 AND weekday <= 6", name="ck_work_schedules_weekday"
        ),
    )
