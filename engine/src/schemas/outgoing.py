from typing import Any

from pydantic import BaseModel, Field


class OutgoingMessage(BaseModel):
    """Ответ провайдеру."""

    user_id: int
    channel: str
    chat_id: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
