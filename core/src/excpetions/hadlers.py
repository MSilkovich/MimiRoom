from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from .base import BaseInnerException
from .exception_type import ExceptionType


def register_exception_handlers(app: FastAPI) -> None:
    """Глобальные обработчики ошибок для всего приложения."""

    @app.exception_handler(BaseInnerException)
    async def _handle_inner(request: Request, exc: BaseInnerException) -> JSONResponse:
        content: dict = {
            "code": exc.code.value,
            "message": exc.message,
        }
        if exc.public_extra:
            content["extra"] = exc.public_extra
        return JSONResponse(status_code=exc.status_code, content=content)

    # NOTE: Добавлять новые исключения ЗДЕСЬ, но не ниже Exception

    @app.exception_handler(HTTPException)
    async def _handle_http(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"code": ExceptionType.UNKNOWN_ERROR, "message": exc.detail})

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:

        return JSONResponse(status_code=500, content={"code": ExceptionType.UNKNOWN_ERROR, "message": "Внутренняя ошибка сервера"})
