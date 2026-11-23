"""Реестр инструментов: JSON-схемы для LLM + handlers.

Каждый инструмент описывается:
- schema — OpenAI function-calling схема (name, description, parameters)
- handler — асинхронная функция, реализованная в handlers/

Ссылки на услугу/мастера передаются как ``id`` (число) ИЛИ точное название
(строка) — код разрешает их детерминированно (см. ``resolvers``).
"""

from typing import Any, Awaitable, Callable

from .handlers import handlers

ToolHandler = Callable[..., Awaitable[Any]]

REF_DESCRIPTION = (
    "Можно передать id (число) или точное название (строка). "
    "Значения бери из каталога/ответов инструментов, не выдумывай."
)


TOOLS: dict[str, dict[str, Any]] = {
    "get_services": {
        "schema": {
            "type": "function",
            "function": {
                "name": "get_services",
                "description": (
                    "Каталог услуг: id, название, цена, длительность, мастера. "
                    "Вызывай в начале диалога и когда спрашивают про цену/наличие. "
                    "Не выдумывай услуги и цены — только из ответа."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 50},
                        "offset": {"type": "integer", "default": 0},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        "handler": handlers.get_services,
    },
    "find_service": {
        "schema": {
            "type": "function",
            "function": {
                "name": "find_service",
                "description": (
                    "Найти услугу по фразе пользователя с учётом опечаток "
                    "(«стрыжка» → «Стрижка»). Возвращает подходящие услуги с id. "
                    "Если ничего не найдено — вернёт fallback (общую услугу), "
                    "которую можно предложить пользователю. "
                    "Вызывай, когда название услуги неточное или пользователь спрашивает "
                    "«что у вас есть»."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Фраза/название услуги от пользователя",
                        },
                        "limit": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        },
        "handler": handlers.find_service,
    },
    "get_masters": {
        "schema": {
            "type": "function",
            "function": {
                "name": "get_masters",
                "description": (
                    "Список мастеров и их услуг. Можно отфильтровать по услуге. "
                    "Вызывай, когда пользователь спрашивает про мастеров или хочет выбрать."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {
                            "type": ["integer", "string"],
                            "description": f"Услуга (id или название). {REF_DESCRIPTION}",
                        },
                        "limit": {"type": "integer", "default": 100},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        "handler": handlers.get_masters,
    },
    "get_availability": {
        "schema": {
            "type": "function",
            "function": {
                "name": "get_availability",
                "description": (
                    "Свободные слоты под услугу (и при желании мастера) на дату/период. "
                    "Вызывай после того, как известны услуга и дата. "
                    "Не выдумывай время — бери только из ответа."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {
                            "type": ["integer", "string"],
                            "description": f"Услуга (id или название). {REF_DESCRIPTION}",
                        },
                        "master": {
                            "type": ["integer", "string"],
                            "description": (
                                "Мастер (id или имя), если пользователь его выбрал. "
                                "Иначе не передавай — подберём автоматически."
                            ),
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Дата начала YYYY-MM-DD",
                        },
                        "date_to": {
                            "type": "string",
                            "description": (
                                "Дата окончания (включительно) YYYY-MM-DD. "
                                "Не указывай для одного дня."
                            ),
                        },
                        "limit": {"type": "integer", "default": 12},
                    },
                    "required": ["service", "date_from"],
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
                    "Создать бронь на конкретное время. Вызывай ТОЛЬКО после "
                    "подтверждения пользователем услуги, времени и мастера. "
                    "service, master и start_time бери из выбранного слота get_availability/"
                    "find_service. Для нескольких услуг вызывай несколько раз."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {
                            "type": ["integer", "string"],
                            "description": f"Услуга (id или название). {REF_DESCRIPTION}",
                        },
                        "master": {
                            "type": ["integer", "string"],
                            "description": f"Мастер (id или имя). {REF_DESCRIPTION}",
                        },
                        "start_time": {
                            "type": "string",
                            "description": (
                                "Время начала из выбранного слота "
                                "(ISO 8601, напр. 2026-11-24T16:00:00+03:00)."
                            ),
                        },
                        "client_name": {
                            "type": "string",
                            "description": "Имя клиента (для гостя обязательно)",
                        },
                        "client_phone": {
                            "type": "string",
                            "description": "Телефон клиента (для гостя обязателен)",
                        },
                        "pet_id": {
                            "type": "integer",
                            "description": "id питомца из сводки, если назван и есть в системе",
                        },
                        "comment": {
                            "type": "string",
                            "description": "Комментарий: кличка (если нет pet_id), пожелания и т.п.",
                        },
                        "options": {
                            "type": "object",
                            "description": "Доп. данные, формат {\"ключ\": \"значение\"}",
                            "additionalProperties": True,
                        },
                    },
                    "required": ["service", "master", "start_time"],
                    "additionalProperties": False,
                },
            },
        },
        "handler": handlers.create_booking,
    },
    "get_my_appointments": {
        "schema": {
            "type": "function",
            "function": {
                "name": "get_my_appointments",
                "description": (
                    "Записи текущего клиента (ближайшие активные). Вызывай, когда "
                    "спрашивают «когда я записан», «мои записи», чтобы не дублировать."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "include_past": {"type": "boolean", "default": False},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        "handler": handlers.get_my_appointments,
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
