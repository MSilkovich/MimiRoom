from typing import Any

from .exception_type import ExceptionType


class BaseInnerException(Exception):
    """
    Базовое исключение приложения.
    """

    code: ExceptionType  # required
    message: str         # reqired

    # используется только в случаях если ошибка будет возвращена пользователю
    status_code: int = 500
    public_extra: dict | None = None

    def __init__(
        self,
        message: str,
        code: ExceptionType = ExceptionType.UNKNOWN_ERROR,
        status_code: int | None = None,
        public_extra: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code or self.status_code
        self.public_extra = public_extra or {}

        super().__init__(self.message)
