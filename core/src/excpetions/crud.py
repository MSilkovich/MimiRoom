from typing import Any

from .base import BaseInnerException
from .exception_type import ExceptionType


class NotFoundError(BaseInnerException):
    """Ресурс не найден (HTTP 404)."""

    def __init__(
        self,
        message: str = "Ресурс не найден",
        code: ExceptionType = ExceptionType.NOT_FOUND_ERROR,
        public_extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=404,
            public_extra=public_extra,
        )


class ConflictError(BaseInnerException):
    """Конфликт данных (например, дубли одноимённых записей)."""

    def __init__(
        self,
        message: str = "Конфликт данных",
        code: ExceptionType = ExceptionType.UNKNOWN_ERROR,
        public_extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=409,
            public_extra=public_extra,
        )


class ValidationError(BaseInnerException):
    """Неверные входные данные (валидация)."""

    def __init__(
        self,
        message: str = "Неверные входные данные",
        code: ExceptionType = ExceptionType.VALIDATION_ERROR,
        public_extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=422,
            public_extra=public_extra,
        )


class InternalError(BaseInnerException):
    """Внутренняя ошибка сервера."""

    def __init__(
        self,
        message: str = "Внутренняя ошибка сервера",
        code: ExceptionType = ExceptionType.UNKNOWN_ERROR,
        public_extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=500,
            public_extra=public_extra,
        )
