"""Реестр инструментов: JSON-схемы для LLM + handlers.

Каждый инструмент описывается:
- schema — OpenAI function-calling схема (name, description, parameters)
- handler — асинхронная функция, реализованная в handlers/

Добавление нового инструмента:
1. Реализовать handler в src/tools/handlers/handlers.py
2. Зарегистрировать его здесь в TOOLS
"""

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
                    "Получить список услуг с ценами. "
                    "Вызывай когда пользователь спрашивает 'что есть', "
                    "'какие услуги', 'сколько стоит', "
                    "или в начале диалога, чтобы предложить варианты."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": (
                                "Сколько услуг вернуть (максимум). "
                                "По умолчанию 10 — обычно хватает."
                            ),
                            "default": 10,
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Смещение для пагинации. По умолчанию 0.",
                            "default": 0,
                        },
                    },
                    "required": [],
                },
            },
        },
        "handler": handlers.get_services,
    },
    "create_booking": {
        "schema": {
            "type": "function",
            "function": {
                "name": "create_booking",
                "description": (
                    "Создать запись на услугу. "
                    "Вызывай ТОЛЬКО после того, как собраны и подтверждены "
                    "пользователем: дата, время и список услуг. "
                    "Перед вызовом перечисли пользователю всё и спроси "
                    "'Подтверждаете запись?'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": (
                                "Дата записи в формате YYYY-MM-DD, "
                                "например 2026-11-15"
                            ),
                        },
                        "time": {
                            "type": "string",
                            "description": (
                                "Время записи в формате HH:MM:SS, "
                                "например 14:30:00"
                            ),
                        },
                        "services": {
                            "type": "array",
                            "description": (
                                "Список услуг, на которые записывается клиент. "
                                "Каждый элемент содержит service_id "
                                "(из get_services)" # + " и опционально master_id."
                            ),
                            "items": {
                                "type": "object",
                                "properties": {
                                    "service_id": {
                                        "type": "integer",
                                        "description": "ID услуги из get_services",
                                    },
                                    # "master_id": {
                                    #     "type": "integer",
                                    #     "description": (
                                    #         "ID мастера для этой услуги "
                                    #         "(если пользователь назвал мастера)"
                                    #     ),
                                    # },
                                },
                                "required": ["service_id"],
                                "additionalProperties": False,
                            },
                            "minItems": 1,
                        },
                        "pet_id": {
                            "type": "integer",
                            "description": (
                                "ID питомца (если пользователь его назвал "
                                "и он есть в системе)"
                            ),
                        },
                        # "master_id": {
                        #     "type": "integer",
                        #     "description": (
                        #         "ID мастера, если он общий для всех услуг "
                        #         "(передавай только если пользователь "
                        #         "явно назвал мастера)"
                        #     ),
                        # },
                        "comment": {
                            "type": "string",
                            "description": (
                                "Комментарий к записи, что-то что пользователь хотел передать менеджеру, "
                                "например 'Первый визит', 'Нужна стрижка'"
                            ),
                        },
                    },
                    "required": ["date", "time", "services"],
                    "additionalProperties": False,
                },
            },
        },
        "handler": handlers.create_booking,
    },
}


def get_tool_schemas() -> list[dict]:
    """Вернуть список схем всех инструментов для передачи в LLM API."""
    return [t["schema"] for t in TOOLS.values()]


def get_handler(name: str) -> ToolHandler:
    """Вернуть handler по имени инструмента."""
    if name not in TOOLS:
        raise KeyError(f"Unknown tool: {name}")
    return TOOLS[name]["handler"]
