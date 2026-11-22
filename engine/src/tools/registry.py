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
                    "Получить список услуг с ценами, длительностью и мастерами. "
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
                                "По умолчанию 50 — обычно каталога хватает."
                            ),
                            "default": 50,
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
    "get_availability": {
        "schema": {
            "type": "function",
            "function": {
                "name": "get_availability",
                "description": (
                    "Получить реальные свободные слоты мастера по услуге на дату/период. "
                    "Вызывай после get_services, когда известны услуга и дата. "
                    "НЕ выдумывай время и slot_id — бери только из ответа этого инструмента. "
                    "Если свободного времени нет, предложи ближайшие варианты из ответа."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_id": {
                            "type": "integer",
                            "description": "ID услуги из get_services",
                        },
                        "date_from": {
                            "type": "string",
                            "description": (
                                "Дата начала в формате YYYY-MM-DD, например 2026-11-24"
                            ),
                        },
                        "date_to": {
                            "type": "string",
                            "description": (
                                "Дата окончания (включительно) в формате YYYY-MM-DD. "
                                "Не указывай, если нужен один день."
                            ),
                        },
                        "resource_id": {
                            "type": "integer",
                            "description": (
                                "ID мастера, если пользователь явно выбрал мастера. "
                                "Иначе не передавай — будут предложены все мастера услуги."
                            ),
                        },
                    },
                    "required": ["service_id", "date_from"],
                    "additionalProperties": False,
                },
            },
        },
        "handler": handlers.get_availability,
    },
    "create_booking": {
        "schema": {
            "type": "function",
            "function": {
                "name": "create_booking",
                "description": (
                    "Создать бронь на конкретный слот. "
                    "Вызывай ТОЛЬКО после того, как пользователь подтвердил "
                    "услугу, время и мастера, и только с slot_id из get_availability. "
                    "Для нескольких услуг вызывай инструмент несколько раз — по одному слоту на услугу."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "slot_id": {
                            "type": "integer",
                            "description": (
                                "ID слота из ответа get_availability. "
                                "Не придумывай значение."
                            ),
                        },
                        "client_name": {
                            "type": "string",
                            "description": "Имя клиента для записи",
                        },
                        "client_phone": {
                            "type": "string",
                            "description": "Телефон клиента для связи",
                        },
                        "comment": {
                            "type": "string",
                            "description": (
                                "Комментарий к записи: кличка питомца, пожелания, "
                                "«первый визит» и т.п."
                            ),
                        },
                    },
                    "required": ["slot_id", "client_name", "client_phone"],
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
