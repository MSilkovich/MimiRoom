# MimiRoom — TG-бот (адаптер Telegram)

Telegram-бот, который принимает сообщения пользователя, передаёт их в `engine`
через Redis Stream и возвращает пользователю ответ LLM.

```
Telegram <-> tg-bot <--[bot:tasks]--> engine <--[LLM]--> engine <--[bot:responses]--> tg-bot
                 \-- HTTP --> core (привязка / поиск связки Telegram <-> user_id)
```

## Что умеет

- `/start` — приветствие и статус привязки.
- `/start <PAYLOAD>` (deep-link `https://t.me/<bot>?start=PAYLOAD`) — привязка
  Telegram к аккаунту из личного кабинета (core `POST /api/v0.0.1/users/link`).
- Любое текстовое сообщение:
  1. резолвит внутренний `user_id` по Telegram-id (с кэшем в Redis, TTL 30 мин);
  2. публикует задачу в `bot:tasks`;
  3. фоновый consumer читает `bot:responses` и отправляет ответ пользователю.

## Структура

```
tg/app/bot/
├── config/                # настройки (pydantic-settings, .env как в engine/core)
│   ├── __init__.py        # load_dotenv()
│   ├── project_config.py  # PROJECT_NAME, VERSION
│   ├── logging_config.py  # LOG_*
│   ├── telegram_config.py # BOT_TOKEN, DEV, WEBHOOKS...
│   ├── redis_config.py    # REDIS_*, имена стримов, TTL кэша
│   └── core_config.py     # CORE_BASE_URL, CORE_SERVICE_SECRET...
├── services/
│   ├── redis_client.py    # singleton Redis + consumer group ответов
│   ├── core_client.py     # HTTP-клиент core + сервисный JWT
│   ├── link_cache.py      # кэш связки external_id -> user_id
│   ├── task_publisher.py  # XADD в bot:tasks
│   └── response_consumer.py # XREADGROUP bot:responses -> Telegram
├── handlers/
│   ├── cmds/start.py      # /start + привязка
│   └── messages/chat.py   # текстовые сообщения
├── middlewares/           # проверки чата/пользователя
├── utils/                 # логирование, deep-link парсер, callback-data
├── errors/                # обработчик ошибок aiogram
└── main.py                # точка входа
```

## Конфигурация

Все переменные — в `tg/.env` (пример: `tg/.env.example`).

| Переменная | Назначение |
|---|---|
| `BOT_TOKEN` | токен бота (обязательно) |
| `DEV` | `true` — long polling, вебхук не ставится |
| `WEBHOOKS`, `WEBHOOK_URL`, `WEBHOOK_SECRET_TOKEN` | режим вебхука (порт 8080) |
| `DEVELOPER_ID`, `TEST_SERVER` | служебные настройки aiogram |
| `CORE_BASE_URL` | адрес core (в docker — `http://core:30010`) |
| `CORE_SERVICE_SECRET` | секрет сервисных JWT (= `core.SERVICE_JWT_SECRET`) |
| `CORE_PROVIDER` | `telegram` |
| `REDIS_HOST/PORT/PASSWORD/DB` | Redis |
| `REDIS_TASK_STREAM_NAME` | входной стрим engine (`bot:tasks`) |
| `REDIS_RESPONSE_STREAM_NAME` | выходной стрим engine (`bot:responses`) |
| `REDIS_RESPONSE_GROUP_NAME` | своя consumer group бота (`tg-bot`) |
| `REDIS_RESPONSE_CONSUMER_NAME` | имя consumer'а (`tg-bot-1`) |
| `LINK_CACHE_TTL_SEC` | TTL кэша связки (1800 = 30 мин) |

> `REDIS_TASK_STREAM_NAME` и `REDIS_RESPONSE_STREAM_NAME` ДОЛЖНЫ совпадать с
> `engine/.env` (`REDIS_STREAM_NAME`, `REDIS_RESPONSE_STREAM_NAME`).

## Запуск

### Локально

```bash
cd tg
cp .env.example .env        # заполнить BOT_TOKEN и REDIS_*/CORE_*
python -m venv venv
venv/Scripts/pip install -r requirements.txt
venv/Scripts/python app/bot/main.py
```

### Docker

`docker/docker-compose.tg.yaml` добавляет сервис `tg` (включён в общий
`docker-compose.yaml`). Использует `tg/.env`.

## Контракт с engine

### Задача (tg -> engine, стрим `bot:tasks`)

Поля = `engine.src.schemas.incoming.IncomingMessage`, все значения строками:

| Поле | Значение |
|---|---|
| `user_id` | внутренний id пользователя в core |
| `provider` | `telegram` |
| `channel` | id чата Telegram (`message.chat.id`) |
| `external_id` | id пользователя Telegram |
| `text` | текст сообщения |
| `message_id` | id сообщения Telegram |
| `received_at` | ISO-8601 UTC |

Историю диалога (`dialog:{user_id}:{channel}`) ведёт сам engine
(`RedisMemoryStore`). Бот её **не** дублирует, чтобы не задвоить контекст LLM.

### Ответ (engine -> tg, стрим `bot:responses`)

Бот читает своей consumer group `tg-bot`, фильтрует `provider == telegram`,
берёт `channel` и `text` и отправляет в Telegram. `original_message_id`
используется только для логов.

## Привязка Telegram (deep-link)

1. ЛК (frontend/core) формирует ссылку `https://t.me/<bot>?start=<PAYLOAD>`.
2. Пользователь открывает бота, приходит `/start <PAYLOAD>`.
3. Бот разбирает payload (`utils/deep_link.py`), вызывает core
   `POST /api/v0.0.1/users/link` и кладёт связку в Redis-кэш.

Поддерживаемые форматы payload (Telegram разрешает только `A-Za-z0-9_-`,
до 64 символов, поэтому «сырой» `user_id=1&token=...` не пройдёт):

- base64url от JSON `{"user_id": 1, "token": "<link-token>"}`;
- base64url от query `user_id=1&token=<link-token>`;
- компактно `1:<token>` (или `1_<token>`, `1-<token>`);
- просто `<code>` (одноразовый код) — тогда `user_id` должен определить core.

### Требования к core (НЕ реализовано в core, нужно добавить)

1. **`GET /api/v0.0.1/users/link?provider=telegram&external_id=<id>`** — ручки
   нет. Бот дергает её на каждое сообщение (результат кэшируется на 30 мин).

   Ожидаемый ответ `200 OK`:
   ```json
   {
     "user_id": 42,
     "provider": "telegram",
     "external_id": "123456789",
     "options": {},
     "user": {                       // опционально, для приветствия
       "user_id": 42,
       "name": "Иван",
       "surname": "Иванов",
       "phone": "+7...",
       "email": "user@example.com"
     }
   }
   ```
   - `user_id` — **обязательное** поле (бот кладёт его в `IncomingMessage.user_id`);
   - если связки нет — `404` (бот поймёт «не привязан» и не закэширует надолго);
   - авторизация — **сервисный** токен (как у engine);
   - ⚠️ в core уже есть `GET /users/{pk}`; чтобы `link` не перехватился как
     `pk="link"`, новый роут надо объявить **до** `GET /users/{pk}` или
     использовать отдельный путь (например, `/users/link/by-external`).

2. **`POST /api/v0.0.1/users/link`** — существует, но:
   - защищён только пользовательским access-токеном
     (`Security(auth_bearer_scheme)` + `get_current_user`), а TG-бот — сервис.
     Нужен либо доступ по сервисному токену, либо передача пользовательского
     `link-token` из deep-link (бот уже умеет передавать его как Bearer).
   - тело требует `user_id` (`UserLinkCreate`), но не проверяет, что `user_id`
     совпадает с субъектом токена. Для безопасности `user_id` лучше брать из
     подписанного токена/одноразового кода, а не из тела.
   - `UserLinkRead` не содержит `user_id` — для единообразия стоит добавить.

3. **Одноразовый link-code** (рекомендуется): из-за лимита 64 символа ссылка
   не может нести длинный JWT. Лучше, чтобы ЛК/`core` выдавали короткий
   одноразовый код, а `POST /users/link` принимал `code` и сам находил
   пользователя (срок жизни 1–5 мин, одноразовый).

## Нестыковки в других сервисах (не менял)

- `POST`/`GET /users/link` — см. раздел выше.
- `engine/.env`: `DIALOG_TTL_SEC=900` (15 мин), хотя TTL диалога задуман
  30 мин. Кэш связки в боте — 1800 с. Менять `engine/.env` не стал.
- `core`/`engine` healthcheck: в compose используется `curl -f GET /healthcheck`,
  а ручки объявлены как `POST`. `GET` вернёт 405 → контейнер будет `unhealthy`.
  Бот зависит только от `redis`, но это стоит поправить в compose/ручках.
- `tg` в `docker-compose.yaml` был закомментирован, а `docker-compose.tg.yaml`
  объявлял сервис `tg-bot` вместо `tg` — исправлено в рамках tg.
- `engine` читает `summary` из `GET /api/v0.0.1/users/{id}/summary` без проверки
  HTTP-статуса: при 404 парсинг `Summary(**json)` упадёт. На стороне engine
  стоит обработать.

## Безопасность

- `BOT_TOKEN` и `CORE_SERVICE_SECRET` — только в `.env` (в git не попадают).
- Deep-link токен/код должен быть короткоживущим и одноразовым.
