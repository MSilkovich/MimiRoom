"""Прикладные исключения и обработчики ошибок FastAPI."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


class NotFoundError(HTTPException):
    """Ресурс не найден (HTTP 404)."""

    def __init__(self, detail: str = "Ресурс не найден"):
        super().__init__(status_code=404, detail=detail)


class ConflictError(HTTPException):
    """Конфликт данных (например, дубли одноимённых записей)."""

    def __init__(self, detail: str = "Конфликт данных"):
        super().__init__(status_code=409, detail=detail)


class ValidationError(HTTPException):
    """Неверные входные данные (валидация)."""

    def __init__(self, detail: str = "Неверные входные данные"):
        super().__init__(status_code=422, detail=detail)


class InternalError(HTTPException):
    """Внутренняя ошибка сервера."""

    def __init__(self, detail: str = "Внутренняя ошибка сервера"):
        super().__init__(status_code=500, detail=detail)


class UnauthorizedError(HTTPException):
    """В контексте нет аутентифицированного пользователя (HTTP 401).

    Кидается guarded-репозиторием, если запись в БД пытаются выполнить без
    пользователя в контексте (см. src/context.py). Это страховочный механизм:
    нормальный поток для защищённых операций уже отсекается на уровне
    зависимости ``get_current_user``.
    """

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=401,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Глобальные обработчики ошибок для всего приложения."""

    @app.exception_handler(NotFoundError)
    async def _handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(ConflictError)
    async def _handle_conflict(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(ValidationError)
    async def _handle_validation(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(InternalError)
    async def _handle_internal(request: Request, exc: InternalError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(HTTPException)
    async def _handle_http(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера"})


class AuthError(Exception):
    def __init__(self, detail: str = ""):
        self.detail = detail


class InvalidCredentialsError(AuthError):
    ...


class InvalidTokenError(AuthError):
    ...


class UserAlreadyExistsError(AuthError):
    ...


class PermissionDeniedError(AuthError):
    ...
