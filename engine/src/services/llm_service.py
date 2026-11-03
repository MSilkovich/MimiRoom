from typing import Protocol, List, Optional
from pydantic import BaseModel


class ToolCall(BaseModel):
    name: str
    arguments: dict


class LLMResponse(BaseModel):
    text: Optional[str] = None
    tool_calls: List[ToolCall] = []


class LLMClient(Protocol):
    async def chat(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        ...
