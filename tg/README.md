# MimiRoom — TG-бот (адаптер Telegram)

Telegram-бот, который принимает сообщения пользователя, передаёт их в `engine`
через Redis Stream и возвращает пользователю ответ LLM.

```
Telegram <-> tg-bot <--[bot:tasks]--> engine <--[LLM]--> engine <--[bot:responses]--> tg-bot
                 \-- HTTP --> core (привязка / поиск связки Telegram <-> user_id)
```

## Что умеет

- `/start` — приветствие и статус привязки.
- `/start <code>` (deep-link `https://t.me/<bot>?start=<code>`) — привязка
  Telegram к аккаунту из ЛК через одноразовый короткий код.
- Любое текстовое сообщение (в т.ч. от **непривязанного** пользователя):
  1. резолвит внутренний `user_id` по Telegram-id (кэш в Redis, TTL 30 мин);
     если не привязан — работает как гость (`user_id=0`);
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
├── utils/                 # логирование, разбор кода /start, callback-data
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

## Привязка Telegram (deep-link, одноразовый код)

1. Пользователь в ЛК нажимает «Привязать Telegram».
2. Фронт вызывает core `POST /api/v0.0.1/users/link/code` (access-токен).
   Core генерирует короткий одноразовый код и кладёт его в Redis
   (`tg:link_code:<code>` → `user_id|provider`) с TTL `LINK_CODE_TTL_SEC`
   (по умолчанию 300 с). Ответ: `{code, expires_in, deep_link?}`;
   `deep_link` собирается, если в core задан `TG_BOT_USERNAME`.
3. Пользователь открывает `https://t.me/<bot>?start=<code>`.
4. Бот отправляет код в core `POST /api/v0.0.1/users/link/code/consume`
   (сервисный токен) вместе со своим `external_id`. Core атомарно забирает
   код из Redis, создаёт `UserLink` и возвращает связку.
5. Бот кэширует `external_id -> user_id` на 30 минут.

Payload `/start` — это **только** одноразовый код (алфавит `A-Z a-z 0-9`,
≤64 символов). Других способов привязки бот не поддерживает: access-токены,
base64/JSON/query-полезные нагрузки и прочие форматы отклоняются.

> Код в БД не хранится: это временный секрет в Redis, одноразовый и с TTL.

## API core по привязкам

- `GET /api/v0.0.1/users/link?provider=&external_id=` — **access или service**.
  Access получает только свою связку, service — любую.
- `GET /api/v0.0.1/users/link/all` — список связок текущего пользователя (access).
- `POST /api/v0.0.1/users/link` — создать/перепривязать (access; `user_id` из токена).
- `PUT /api/v0.0.1/users/link/{link_id}` — обновить свою (access).
- `DELETE /api/v0.0.1/users/link/{link_id}` — удалить свою (access).
- `POST /api/v0.0.1/users/link/code` — выпустить одноразовый код (access).
- `POST /api/v0.0.1/users/link/code/consume` — обменять код на связку (service).

`UserLinkRead` содержит `id` и `user_id`.

## Анонимный пользователь (без привязки)

Бот не блокирует непривязанных:
- `user_id` для engine = `0` (гость);
- `channel` = `<chat_id>:<external_id>`, чтобы в группах не смешивать историю
  разных гостей (для привязанных — просто `<chat_id>`);
- `core GET /users/0/summary` отдаёт гостевую сводку, чтобы engine не падал;
- запись создаётся с `client_id=null`, а дополнительная информация может
  храниться в `Book.options` (JSONB).

## Нестыковки в других сервисах

- **[исправлено]** `engine create_booking` теперь передаёт `client_id` для
  привязанного пользователя (`user_id > 0`) и `options` для доп. данных гостя;
  в схеме tool появилось поле `options`.
- **[исправлено]** в `EMPTY_SUMMARY` исправлена опечатка `optinons` → `options`.
- `engine/.env`: `DIALOG_TTL_SEC=900` (15 мин), хотя TTL диалога задуман
  30 мин. Кэш связки в боте — 1800 с. Менять `engine/.env` не стал.
- **[исправлено]** healthcheck `core`/`engine`: теперь `GET /healthcheck` отдаёт
  реальный снимок фонового монитора (БД/Redis/core/LLM), без открытия
  соединений на каждый HTTP-запрос.
- `engine/.env`: `DIALOG_TTL_SEC=900` (15 мин), хотя TTL диалога задуман
  30 мин. Кэш связки в боте — 1800 с. Менять `engine/.env` не стал.
- `engine` читает `summary` из `GET /api/v0.0.1/users/{id}/summary` без проверки
  HTTP-статуса — **исправлено**: 404 → `None`, 4xx/5xx/сеть → `BackendError`.

## Безопасность

- `BOT_TOKEN` и `CORE_SERVICE_SECRET` — только в `.env` (в git не попадают).
- Deep-link токен/код должен быть короткоживущим и одноразовым.
