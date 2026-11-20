from typing import Protocol, runtime_checkable

from src.schemas.llm import LLMResponse, ToolCall


@runtime_checkable
class LLMClient(Protocol):
    """
    Единый интерфейс для любого LLM-провайдера.

    Реализации (OpenAI, GigaChat, Ollama) нормализуют ответ провайдера
    в LLMResponse и бросают LLMError при сбоях.
    """

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        *,
        temperature: float | None = None,
    ) -> LLMResponse:
        ...
