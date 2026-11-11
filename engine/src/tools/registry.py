"""Реестр инструментов: JSON-схемы для LLM + handlers."""

from typing import Any, Awaitable, Callable

from .handlers import handlers


ToolHandler = Callable[..., Awaitable[Any]]


TOOLS: dict[str, dict[str, Any]] = {
    "get_services": {
        "schema": {
            "type": "function",
            "function": {
                "name": "get_services",
                "description": (
                    "Возвращает список доступных услуг с ценами. "
                    "Используй, когда пользователь спрашивает, что есть, "
                    "или в начале записи, чтобы предложить варианты."
                ),
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        "handler": handlers.get_services,
    },
}


def get_tool_schemas() -> list[dict]:
    return [t["schema"] for t in TOOLS.values()]


def get_handler(name: str) -> ToolHandler:
    if name not in TOOLS:
        raise KeyError(f"Unknown tool: {name}")
    return TOOLS[name]["handler"]
