from abc import ABC
from typing import Any

from .base import BaseInnerException
from .exception_type import ExceptionType


class AuthError(ABC, BaseInnerException):
    """Базовый класс для ошибок аутентификации/авторизации."""

    status_code: int = 401

    def __init__(
        self,
        message: str = "Ошибка аутентификации",
        code: ExceptionType = ExceptionType.UNKNOWN_ERROR,
        status_code: int | None = None,
        public_extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            public_extra=public_extra,
        )


class InvalidCredentialsError(AuthError):
    """Неверная пара логин/пароль."""

    def __init__(
        self,
        message: str = "Неверные учётные данные",
        public_extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ExceptionType.INVALID_CREDENTIALS_ERROR,
            status_code=401,
            public_extra=public_extra,
        )


class InvalidTokenError(AuthError):
    """Токен отсутствует, повреждён или неверного формата."""

    def __init__(
        self,
        message: str = "Недействительный токен",
        public_extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ExceptionType.INVALID_TOKEN_ERROR,
            status_code=401,
            public_extra=public_extra,
        )


class UserAlreadyExistsError(AuthError):
    """Пользователь с такими данными уже зарегистрирован."""

    def __init__(
        self,
        message: str = "Пользователь уже существует",
        public_extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ExceptionType.USER_ALREADY_EXISTS_ERROR,
            status_code=409,
            public_extra=public_extra,
        )


class PermissionDeniedError(AuthError):
    """Недостаточно прав для выполнения операции."""

    def __init__(
        self,
        message: str = "Недостаточно прав",
        public_extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ExceptionType.PERMISSION_DENIED_ERROR,
            status_code=403,
            public_extra=public_extra,
        )


class UnauthorizedError(BaseInnerException):
    """В контексте нет аутентифицированного пользователя."""

    def __init__(
        self,
        message: str = "Authentication required",
        public_extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ExceptionType.UNAUTHORIZED_ERROR,
            status_code=401,
            public_extra=public_extra,
        )
