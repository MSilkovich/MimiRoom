# МиМиРум · frontend 0.5.0

Отдельный клиентский кабинет с выбором свободных окошек и рабочее приложение администратора, менеджера и грумера. Интерфейс на ES modules, сервер на Node.js, без обязательных внешних зависимостей.

## Запуск

```sh
cd frontend
npm ci
npm start
```

Node.js 22+. Откройте http://127.0.0.1:4180/client/ или http://127.0.0.1:4180/studio/. Сначала доступен деморежим. Нажмите вход в клиентском профиле либо откройте «Настройки» в CRM и войдите под существующим пользователем core. Регистрация создаёт клиента; права сотрудника выдаёт администратор.

Для настоящих данных запустите core с PostgreSQL/Redis по инструкции команды backend. По умолчанию Node-сервер передаёт `/api/v0.0.1/*` на `http://127.0.0.1:30010`. Адрес API в форме можно оставить пустым — запросы пойдут через этот прокси, без настройки CORS.

При необходимости создайте `frontend/.env.local` на основе `.env.example`:

```dotenv
CORE_API_URL=http://127.0.0.1:30010
SUPPORT_PORT=4180
SUPPORT_HOST=127.0.0.1
AI_ENABLED=false
TELEGRAM_ENABLED=false
```

`CORE_API_URL` — адрес сервера core, без `/api/v0.0.1`. Если браузер подключается к другому origin напрямую, CORS должен разрешить backend. Не добавляйте ключи, токены, `.env.local` и `.data/` в Git. Demo данные сохраняются в localStorage, live токены — в sessionStorage текущей вкладки.

## Проверка

```sh
npm run check
npm run package
npm test
npm run test:browser
```

`package` требует Python 3 и создаёт автономные демо HTML. Для проверки браузером установите Playwright отдельно: `npm install --no-save --package-lock=false playwright@1.62.1`, затем `npx playwright install chromium` (или используйте Chrome через `CHROME_PATH`). Рабочее приложение запускается через `npm start`, автономные HTML предназначены для демонстрации.

## Docker

```sh
docker build -t mimiroom-frontend ./frontend
docker run --rm -p 127.0.0.1:4180:4180 -e CORE_API_URL=http://host.docker.internal:30010 mimiroom-frontend
```

На Linux адрес core укажите явно; `host.docker.internal` может требовать host-gateway. Для существующего compose есть необязательный overlay `docker/docker-compose.frontend.yaml`; используйте его вместе с основным compose из каталога `docker/`.

[Что добавлено](docs/FRONTEND-UPDATE.md) · [Разработчикам](docs/DEVELOPMENT.md) · [Ограничения и следующие шаги](docs/BACKEND-NEXT.md) · [ИИ-поддержка](docs/AI-SUPPORT.md)
