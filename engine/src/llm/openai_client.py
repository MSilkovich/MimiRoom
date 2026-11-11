"""LLM-клиент для Qwen3.7 Flash через OpenAI-совместимый API."""

import json
from src.logging import get_logger
from typing import Any

from openai import AsyncOpenAI, APIStatusError, APITimeoutError, RateLimitError

from config.llm import settings_llm
from src.llm.base import LLMClient, LLMError
from src.schemas.llm import LLMResponse, ToolCall

logger = get_logger(__name__)


class QwenClient(LLMClient):
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings_llm.LLM_API_KEY,
            base_url=settings_llm.LLM_BASE_URL,
            timeout=settings_llm.LLM_TIMEOUT_SEC,
            max_retries=0,  # ретраи делаем сами, чтобы контролировать 429
        )
        self._model = settings_llm.LLM_MODEL

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        *,
        temperature: float | None = None,
        tool_choice: str | dict | None = None,
        parallel_tool_calls: bool = False,
    ) -> LLMResponse:
        request_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature if temperature is not None else 0.0,
            "max_tokens": settings_llm.LLM_MAX_TOKENS,
        }
        if tools:
            request_kwargs["tools"] = tools
            request_kwargs["tool_choice"] = tool_choice or "auto"
            request_kwargs["parallel_tool_calls"] = parallel_tool_calls

        logger.debug(
            "LLM request: model=%s, messages=%d, tools=%s, tool_choice=%s",
            self._model,
            len(messages),
            [t["function"]["name"] for t in tools] if tools else None,
            request_kwargs.get("tool_choice"),
        )

        try:
            response = await self._client.chat.completions.create(**request_kwargs)
        except RateLimitError as e:
            logger.warning("Qwen rate limit hit: %s", e)
            raise LLMError(f"Rate limit: {e}") from e
        except APITimeoutError as e:
            logger.error("Qwen timeout: %s", e)
            raise LLMError(f"Timeout: {e}") from e
        except APIStatusError as e:
            logger.error("Qwen API error %s: %s", e.status_code, e.message)
            raise LLMError(f"API error {e.status_code}: {e.message}") from e
        except Exception as e:
            logger.exception("Qwen unexpected error")
            raise LLMError(f"Unexpected: {e}") from e

        choice = response.choices[0]
        message = choice.message
        finish_reason = choice.finish_reason

        logger.info(
            "LLM response: finish_reason=%s, tool_calls=%d, usage=%s",
            finish_reason,
            len(message.tool_calls or []),
            response.usage.model_dump() if response.usage else None,
        )

        if finish_reason == "length":
            logger.error("Response truncated by max_tokens")
            raise LLMError("Response truncated: increase LLM_MAX_TOKENS")

        tool_calls: list[ToolCall] = []
        for tc in message.tool_calls or []:
            try:
                args = json.loads(
                    tc.function.arguments) if tc.function.arguments else {}
                is_valid = True
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in tool args: %s",
                               tc.function.arguments)
                args = {"_raw": tc.function.arguments}
                is_valid = False

            tool_calls.append(
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=args,
                    is_valid=is_valid,
                )
            )

        return LLMResponse(
            text=message.content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=response.usage.model_dump() if response.usage else None,
            raw=response.model_dump() if settings_llm.LLM_DEBUG_RAW else None,
        )
