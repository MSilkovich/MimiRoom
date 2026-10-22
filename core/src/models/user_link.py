from datetime import datetime
from typing import TYPE_CHECKING, Any
from sqlalchemy import (
    DateTime, Enum as SAEnum, ForeignKey, String, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base
from .enums.provider import Provider

if TYPE_CHECKING:
    from .user import User


class UserLink(Base):
    __tablename__ = "user_link"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider: Mapped[Provider] = mapped_column(
        SAEnum(Provider, name="provider_enum"),
        nullable=False,
    )

    external_id: Mapped[str] = mapped_column(String(64), nullable=False)

    options: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    user: Mapped["User"] = relationship("User", back_populates="links")

    __table_args__ = (
        # 1 user = 1 provider = 1 external id
        UniqueConstraint("user_id", "provider",
                         name="uq_user_link_user_provider"),
        UniqueConstraint("provider", "external_id",
                         name="uq_user_link_provider_external"),
    )
