"""Оркестратор: LLM + tools + memory. Вызывается из handlers.process_message."""

import json
import logging
from typing import Any

from src.logging import get_logger
from src.prompts.helper import load_prompt
from src.schemas.llm import LLMResponse, Role, ToolResult
from src.schemas.incoming import IncomingMessage
from src.llm.base import LLMClient
from src.exceptions import LLMError
from src.memory.base import MemoryStore
from src.tools.registry import get_handler, get_tool_schemas

logger = get_logger(__name__)

MAX_ITERATIONS = 3  # защита от бесконечного цикла tool_calls


class LLMService:
    def __init__(self, client: LLMClient, memory: MemoryStore) -> None:
        self._client = client
        self._memory = memory
        self._system_prompt = load_prompt("system.txt")
        self._tools = get_tool_schemas()

    async def process(self, task: IncomingMessage) -> str:
        """Обработать одно входящее сообщение и вернуть текст ответа."""
        history = await self._memory.load(task.user_id, task.channel)

        messages: list[dict] = [
            {"role": Role.SYSTEM, "content": self._system_prompt},
            *history,
            {"role": Role.USER, "content": task.text},
        ]

        # сохраняем входящее сообщение (когда будет реальная память)
        await self._memory.append(
            task.user_id, task.channel, {
                "role": Role.USER, "content": task.text}
        )

        final_text: str | None = None

        for iteration in range(MAX_ITERATIONS):
            response = await self._client.chat(messages, tools=self._tools)

            if not response.tool_calls:
                final_text = response.text or ""
                break

            # добавляем assistant-сообщение с tool_calls в историю запроса
            messages.append(self._assistant_tool_call_message(response))

            # выполняем все tool_calls последовательно
            for call in response.tool_calls:
                result = await self._execute_tool(call, task.user_id)
                messages.append(self._tool_result_message(result))

        if final_text is None:
            logger.error("Exceeded MAX_ITERATIONS without final answer")
            final_text = "Извините, не удалось обработать запрос. Попробуйте позже."

        await self._memory.append(
            task.user_id, task.channel, {
                "role": Role.ASSISTANT, "content": final_text}
        )
        return final_text

    async def _execute_tool(self, call, user_id: int) -> ToolResult:
        if not call.is_valid:
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                content=json.dumps({"error": "invalid_arguments"}),
                is_error=True,
            )
        try:
            handler = get_handler(call.name)
            result = await handler(user_id=user_id, **call.arguments)
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                content=json.dumps(result, ensure_ascii=False),
            )
        except Exception as e:
            logger.exception("Tool %s failed", call.name)
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                content=json.dumps({"error": str(e)}, ensure_ascii=False),
                is_error=True,
            )

    def _assistant_tool_call_message(self, response: LLMResponse) -> dict:
        return {
            "role": Role.ASSISTANT,
            "content": response.text or "",
            "tool_calls": [
                {
                    "id": c.id,
                    "type": "function",
                    "function": {
                        "name": c.name,
                        "arguments": json.dumps(c.arguments, ensure_ascii=False),
                    },
                }
                for c in response.tool_calls
            ],
        }

    def _tool_result_message(self, result: ToolResult) -> dict:
        return {
            "role": Role.TOOL,
            "tool_call_id": result.tool_call_id,
            "content": result.content,
        }
