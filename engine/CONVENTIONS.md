# Mimiroom Engine — Соглашения проекта

## Общее описание

Mimiroom Engine — backend-сервис обработки сообщений пользователей через LLM (Large Language Model).
Адаптеры (TG бот, бот в Max, ВК и т.д.) публикуют сообщение пользователя в Redis Stream (`bot:tasks`),
Engine читает поток, обрабатывает сообщение через LLM с возможностью вызова инструментов (tools),
и публикует ответ LLM обратно в Redis Stream (`bot:responses`), откуда адаптер его забирает.

```
Adapter ──[bot:tasks]──> Engine ──[LLM]──> Engine ──[bot:responses]──> Adapter
                              │
                              └──[Tools: HTTP → Backend API]
```

## Архитектура

Проект использует **слоистую архитектуру** без жёсткой привязки к конкретному шаблону. Ключевые слои:

1. **Config** — настройки через `pydantic-settings`, загружаются из `.env`
2. **App (FastAPI)** — точки входа: lifespan (startup/shutdown), маршруты
3. **Services** — бизнес-логика: consumer Redis Stream, LLM-оркестратор
4. **LLM layer** — абстракция над LLM-провайдерами (Protocol + реализации)
5. **Memory** — абстракция хранилища истории диалога (Protocol + реализации)
6. **Tools** — реестр инструментов, которые LLM может вызывать
7. **Schemas** — Pydantic-модели для входящих/исходящих данных
8. **Prompts** — system prompt и утилиты для их загрузки
9. **Logging** — централизованная настройка логирования

## Структура проекта

```
├── config/
│   ├── __init__.py                  # загрузка .env (load_dotenv)
│   ├── project_config.py            # PROJECT_NAME, VERSION
│   ├── logging/
│   │   ├── __init__.py              # экспорт settings_logging
│   │   └── logging_config.py        # LOG_LEVEL, LOG_CONSOLE, LOG_FILE...
│   ├── redis/
│   │   ├── __init__.py              # экспорт settings_redis
│   │   └── redis_config.py          # REDIS_HOST, REDIS_PORT, Stream/Group...
│   ├── llm/
│   │   ├── __init__.py              # экспорт settings_llm
│   │   └── llm_config.py            # LLM_PROVIDER, LLM_MODEL, API_KEY...
│   └── backend/
│       ├── __init__.py              # экспорт settings_backend
│       └── backend_config.py        # BACKEND_BASE_URL, SERVICE_TOKEN...
│
├── src/
│   ├── __init__.py
│   ├── exceptions.py                # LLMError — базовая ошибка LLM-слоя
│   │
│   ├── logging/
│   │   ├── __init__.py              # экспорт setup_logging, get_logger
│   │   ├── logging.py               # _build_log_config, setup_logging
│   │   └── logger.py                # get_logger(name) — фабрика логгеров
│   │
│   ├── schemas/
│   │   ├── __init__.py              # экспорт всех схем
│   │   ├── incoming.py              # IncomingMessage
│   │   ├── outgoing.py              # OutgoingMessage
│   │   ├── llm.py                   # LLMResponse, Role, ToolCall, ToolResult
│   │   └── enums/
│   │       └── provider.py          # Provider (telegram)
│   │
│   ├── apps/
│   │   └── engine/
│   │       ├── __init__.py          # "Core application"
│   │       ├── main.py              # FastAPI app factory (get_application)
│   │       ├── lifespan.py          # startup/shutdown (Redis, logging)
│   │       ├── routes.py            # сборка APIRouter из всех роутеров
│   │       └── routers/
│   │           ├── __init__.py      # экспорт chat_router
│   │           ├── staff.py         # /healthcheck
│   │           └── chat.py          # (TODO) эндпоинты чата
│   │
│   ├── services/
│   │   ├── __init__.py              # экспорт run_consumer, publish_response, redis_*
│   │   ├── redis_connection.py      # singleton Redis client, consumer group
│   │   ├── consumer_service.py      # Redis Stream consumer (drain+loop+janitor)
│   │   ├── llm_service.py           # LLMService.process_message(fields) → OutgoingMessage
│   │   └── output_service.py        # publish_response() → Redis response stream
│   │
│   ├── llm/
│   │   ├── base.py                  # LLMClient Protocol
│   │   ├── factory.py               # create_llm_client()
│   │   └── openai_client.py         # QwenClient — OpenAI-совместимый клиент
│   │
│   ├── memory/
│   │   ├── __init__.py              # экспорт MemoryStore, RedisMemoryStore, NoopMemoryStore
│   │   ├── base.py                  # MemoryStore Protocol
│   │   ├── noop.py                  # NoopMemoryStore (заглушка)
│   │   └── redis_memory.py          # RedisMemoryStore — основная реализация
│   │
│   ├── repositories/
│   │   ├── __init__.py              # экспорт BookingRepository, booking_repository
│   │   ├── base.py                  # BaseRepository — HTTP-клиент к backend API
│   │   └── booking_repository.py    # BookingRepository (get_services, create_booking)
│   │
│   ├── tools/
│   │   ├── registry.py              # TOOLS registry + get_tool_schemas/get_handler
│   │   └── handlers/
│   │       ├── __init__.py          # экспорт handlers
│   │       └── handlers.py          # handlers инструментов → вызывают репозитории
│   │
│   └── prompts/
│       ├── __init__.py              # экспорт load_prompt
│       ├── helper.py                # load_prompt(name) — чтение .md файлов
│       └── system.md                # system prompt
│
├── Dockerfile                       # multi-stage сборка (builder → slim)
├── requirements.txt                 # зависимости
├── .env                             # переменные окружения (в gitignore)
├── .gitignore
├── .dockerignore
└── CONVENTIONS.md
```

## Соглашения

### Общие

- **Язык кода**: английский (имена переменных, функций, классов, комментарии кода).
- **Язык документации**: русский (комментарии в docstring для контекста, CONVENTIONS.md, README).
- **Имена файлов**: snake_case.
- **Имена классов**: PascalCase.
- **Имена функций/методов**: snake_case.
- **Имена констант**: UPPER_SNAKE_CASE.
- **Типизация**: обязательна. Используем `from __future__ import annotations` где уместно, `| None` вместо `Optional`.

### Слои и зависимости

- `config/` → не зависит от `src/`. Может быть импортирован откуда угодно.
- `src/schemas/` → не зависит от других модулей `src/`.
- `src/logging/` → зависит только от `config/`.
- `src/llm/` → зависит от `config/`, `src/schemas/`, `src/exceptions/`.
- `src/tools/` → зависит от `config/`, `src/logging/`.
- `src/services/` → координационный слой, зависит от config, schemas, llm, tools, memory, prompts.
- `src/apps/engine/` → корень приложения, собирает всё вместе.

### Config

- Каждая группа настроек — отдельный класс `Settings(BaseSettings)` в отдельном файле.
- Настройки экспортируются через `__init__.py` модуля как `settings_*` (например, `settings_llm`).
- `.env` загружается один раз в `config/__init__.py`.
- Параметры читаются из переменных окружения; значения по умолчанию задаются в классе.

### Logging

- **Единый логгер** через `get_logger(__name__)`.
- Имя логгера формируется как `{PROJECT_NAME}.{module_path}`.
- Настройка логирования происходит в `src/logging/logging.py`, вызывается один раз в `lifespan.py`.
- Не используем `logging.getLogger()` напрямую — только через `get_logger()`.
- Уровень, консоль/файл, ротацию настраиваем через `config/logging/logging_config.py`.

### FastAPI

- **App factory**: `get_application()` в `main.py` создаёт экземпляр `FastAPI`.
- **Lifespan**: вся инициализация и очистка — в `lifespan.py` (Redis, consumer task, logging).
- **Роутеры** собираются в `routes.py` через `get_apps_router()`.
- Каждый роутер — отдельный файл в `routers/` с собственным `APIRouter`.
- Контроллеры (роутеры) не содержат бизнес-логики — вызывают сервисы.
- Depends используем для кеширования зависимостей в рамках запроса.

### LLM слой

- **LLMClient** — протокол (Protocol), а не абстрактный класс. Любая реализация должна предоставлять `async def chat(...)`.
- Реализации нормализуют ответ провайдера в `LLMResponse`.
- Ошибки провайдера оборачиваются в `LLMError`.
- Фабрика `create_llm_client()` выбирает реализацию по `LLM_PROVIDER` из конфига.
- **QwenClient** — текущая реализация для Qwen3.7 Flash через OpenAI-совместимый API.

### Memory

- **MemoryStore** — протокол с методами `load`, `append`, `clear`.
- **Основная реализация — `RedisMemoryStore`**:
  - Хранит историю в Redis List с ключом `dialog:{user_id}:{channel}`.
  - Каждый элемент — JSON-строка `{"role": "user"/"assistant", "content": "..."}`.
  - TTL = `DIALOG_TTL_SEC` (по умолчанию 900 с = 15 мин). Обновляется при каждом `append()`.
  - Если диалог не пополнялся дольше TTL — Redis удаляет ключ автоматически.
  - `load()` делает `LRANGE 0 -1` и парсит JSON, возвращает список сообщений.
  - `append()` делает `RPUSH` + `EXPIRE`.
  - `clear()` делает `DELETE`.
- **`NoopMemoryStore`** — заглушка для тестов или офлайн-режима.
- **Будущее**: при `append()` можно дублировать сообщение в PostgreSQL для долговременного хранения; `RedisMemoryStore` этого не делает, его задача — быстрая загрузка/запись.

### Tools (Инструменты)

- Реестр `TOOLS` в `registry.py` — словарь, где ключ — имя инструмента, значение — `{"schema": ..., "handler": ...}`.
- `schema` — JSON Schema для OpenAI function calling.
- `handler` — асинхронная функция, реализованная в `handlers/`.
- **Текущие инструменты**:
  1. `get_services` — GET `/api/v0.0.1/services` — список услуг с ценами (limit, offset).
  2. `create_booking` — POST `/api/v0.0.1/book` — создание записи (date, time, services, опционально pet_id, master_id, comment).
- **Цепочка вызова**: LLM → registry.get_handler() → handlers.xxx() → repositories.BookingRepository → BaseRepository._request() → HTTP → Backend API.
- Handlers не делают HTTP-запросы напрямую. За HTTP отвечают репозитории.
- `get_tool_schemas()` — возвращает список схем для передачи в LLM API.
- `get_handler(name)` — возвращает handler по имени.
- Инструменты не должны содержать логику, доступную из основного кода — только то, что LLM должен вызывать самостоятельно.

### Repositories (Репозитории)

- `BaseRepository` — базовый класс с методом `_request(method, path, json, params)`, который ходит в backend API с `X-Service-Token`.
- Конкретные репозитории (например, `BookingRepository`) наследуют `BaseRepository` и добавляют предметные методы.
- Репозитории — единственное место, где делаются HTTP-запросы к backend.
- `booking_repository` — singleton, создаётся на уровне модуля и переиспользуется всеми handlers.

### Consumer (Redis Stream)

- **Входной стрим** (`REDIS_STREAM_NAME`, по умолчанию `bot:tasks`): адаптеры публикуют сообщения пользователей.
- **Consumer group**: `{REDIS_GROUP_NAME}`, consumer: `{REDIS_CONSUMER_NAME}` (уникальный per-инстанс).
- **Выходной стрим** (`REDIS_RESPONSE_STREAM_NAME`, по умолчанию `bot:responses`): engine публикует ответ LLM.
- **Три фазы** работы consumer'а:
  1. **Drain** — дочитываем свои pending-сообщения (id="0").
  2. **Main loop** — читаем новые сообщения (id=">").
  3. **Janitor** — периодически XAUTOCLAIM сообщений мёртвых consumer'ов.
- **Полный цикл обработки одного сообщения**: прочитать из `bot:tasks` → распарсить в `IncomingMessage` → LLM + tools loop → собрать `OutgoingMessage` → опубликовать в `bot:responses` → ACK исходного сообщения.
- ACK делаем только после успешной обработки **и** публикации ответа. Ошибка → сообщение остаётся в PEL.
- `MAX_ITERATIONS = 3` — защита от бесконечного цикла tool_calls.

### Именование и структура

- **Директории** — во множественном числе: `services`, `schemas`, `routers`, `tools`, `handlers`, `prompts`, `enums`.
- **Файлы с настройками** — `{domain}_config.py` (например, `redis_config.py`, `llm_config.py`).
- **Файлы с реализациями** — именуем по основной сущности: `consumer_service.py`, `llm_service.py`, `openai_client.py`.
- **Файлы роутеров** — именуем по домену: `staff.py`, `chat.py`.

### Обработка ошибок

- `LLMError` — базовое исключение LLM-слоя.
- В инструментах (tools): ошибка оборачивается в `ToolResult(is_error=True)`.
- В consumer: ошибка обработки логируется, сообщение **не** ACK-ится (остаётся в PEL для повторной попытки).
- HTTP-ошибки бэкенда логируются в инструментах.

### TODO и незавершённое

Проект находится в активной разработке. Известные TODO:

- `healthcheck` — возвращает `True`, нужна полноценная проверка (Redis, LLM, backend).
- Тесты отсутствуют.
- Provider enum содержит только `TELEGRAM` — будут добавлены другие.
- Долговременное хранение истории диалога в PostgreSQL (дублировать при каждом append()).

## Разработка

### Запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск
uvicorn src.apps.engine.main:app --reload
```

### Docker

```bash
docker build --build-arg ENGINE_PORT=8000 -t mimiroom-engine .
docker run -p 8000:8000 --env-file .env mimiroom-engine
```

### Добавление нового инструмента (tool)

1. Реализовать handler в `src/tools/handlers/handlers.py`.
2. Зарегистрировать в `TOOLS` словаре в `src/tools/registry.py` (schema + handler).
3. Если нужно менять поведение — дополнить `LLMService.process()`.

### Добавление нового LLM-провайдера

1. Реализовать класс, имплементирующий `LLMClient` protocol.
2. Добавить ветку в `create_llm_client()` в `factory.py`.
3. При необходимости — добавить настройки в `config/llm/llm_config.py`.

### Добавление нового роутера

1. Создать файл `routers/{domain}.py` с `router = APIRouter(...)`.
2. Импортировать и включить в `routes.py` через `router.include_router(...)`.
3. Если роутер новый — добавить тег в `openapi_tags` в `main.py`.
