from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from .summary import Summary

from .enums.provider import Provider


class IncomingMessage(BaseModel):
    """Универсальное входящее сообщение от любого провайдера."""

    user_id: int = Field(...,
                         description="Внутренний user_id")
    provider: Provider
    channel: str = Field(...,
                         description="Канал в провайдере (chat/thread id)")
    external_id: str = Field(...,
                             description="external_id пользователя в провайдере")
    text: str = Field(..., min_length=1)
    message_id: str = Field(...,
                            description="ID сообщения в провайдере (для идемпотентности)")
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)
    summary: Summary | None = Field(
        default=None,
        description="Краткая сводка о пользователе",
    )
