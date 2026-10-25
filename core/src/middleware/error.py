from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.apps.core.logging import get_logger

logger = get_logger(__name__)


class ErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            # Логируем полный traceback, но никак не возвращаем его клиенту
            logger.error("Unhandled exception on %s %s",
                         request.method, request.url)
            return JSONResponse(
                status_code=500,
                content={"code": 500, "message": "Внутренняя ошибка сервера"}
            )
