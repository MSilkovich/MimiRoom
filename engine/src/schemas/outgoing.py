from typing import Any

from pydantic import BaseModel, Field

from .enums.provider import Provider


class OutgoingMessage(BaseModel):
    """Ответ провайдеру. Публикуется в response-стрим, откуда адаптер забирает."""

    user_id: int
    provider: Provider
    channel: str = Field(...,
                         description="Канал в провайдере (chat/thread id)")
    external_id: str = Field(...,
                             description="external_id пользователя в провайдере")
    text: str = Field(..., min_length=1)
    original_message_id: str | None = Field(
        default=None,
        description="message_id из IncomingMessage — для идемпотентности/корреляции",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
