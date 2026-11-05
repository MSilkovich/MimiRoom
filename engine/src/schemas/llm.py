"""Схемы LLM-слоя."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(BaseModel):
    id: str = Field(..., description="ID вызова, генерируется LLM")
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool_call_id: str
    name: str
    content: str = Field(...,
                         description="JSON-строка или текст — что вернуть в LLM")
    is_error: bool = False


class LLMResponse(BaseModel):
    text: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    raw: dict[str, Any] | None = Field(
        default=None, description="Сырой ответ провайдера для отладки"
    )

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)
