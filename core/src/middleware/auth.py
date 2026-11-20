from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from config.jwt.jwt_config import settings_jwt
from src.context import SYSTEM_USER, current_user, set_current_user
from src.models import TokenType, User
from src.middleware.service_auth import decode_service_token


auth_bearer_scheme = HTTPBearer(
    auto_error=False, scheme_name="AuthorizationToken")


def decode_token(token: str, expected_type: str | None = None) -> dict:
    """Проверить пользовательский JWT и вернуть его payload."""
    try:
        payload = jwt.decode(token, settings_jwt.JWT_SECRET_KEY, algorithms=[
                             settings_jwt.JWT_ALGORITHM])
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            f"Invalid token: {e}")
    if expected_type and payload.get("type") != expected_type:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            f"Expected {expected_type} token")
    if "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "Token has no subject")
    return payload


def get_unverified_token_payload(token: str) -> dict:
    """Прочитать claims токена без проверки подписи.

    Нужен только для того, чтобы определить *тип* токена (access или service):
    оба типа приходят в одном заголовке ``Authorization: Bearer ...``.
    Доверять данным отсюда нельзя — перед использованием токен обязательно
    проверяется правильным секретом (``decode_token`` / ``decode_service_token``).
    """
    try:
        return dict(jwt.get_unverified_claims(token))
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            f"Invalid token: {e}")


def is_access_token_payload(payload: dict) -> bool:
    """Похож ли payload на пользовательский access-токен."""
    return payload.get("type") == TokenType.ACCESS and "sub" in payload


async def get_user_by_id_or_none(user_id: int) -> User | None:
    from src.dependencies import get_uow_factory
    async with get_uow_factory()() as uow:
        repo = uow.repository(User)
        return await repo.get_single(user_id=user_id)


# ---------- Мидлварь: положить User в ContextVar ----------

class AuthMiddleware(BaseHTTPMiddleware):
    """
    На каждый запрос: если есть Bearer — определяет тип токена и кладёт
    ``User`` в ContextVar (для аудита who_create/who_update).

    - пользовательский access-токен -> реальный пользователь;
    - сервисный токен -> системный пользователь (``SYSTEM_USER``);
    - нет токена / невалидный -> ``None`` (решают конкретные роуты).
    """

    async def dispatch(self, request: Request, call_next):
        header = request.headers.get("Authorization", "")
        user: User | None = None

        if header.lower().startswith("bearer "):
            token = header.split(" ", 1)[1].strip()
            try:
                unverified = get_unverified_token_payload(token)
                if is_access_token_payload(unverified):
                    payload = decode_token(
                        token, expected_type=TokenType.ACCESS)
                    user = await get_user_by_id_or_none(int(payload["sub"]))
                else:
                    # Не access-токен: пробуем как сервисный. Пользовательские
                    # refresh / service токены проверяются внутри
                    # decode_service_token и при несоответствии отсеиваются.
                    decode_service_token(token)
                    user = SYSTEM_USER
            except Exception:
                user = None

        token_ctx = set_current_user(user)
        try:
            response = await call_next(request)
        finally:
            current_user.reset(token_ctx)
        return response


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        auth_bearer_scheme),
) -> User:
    """Зависимость для роутов, доступных только пользователю (access-токен)."""
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    payload = decode_token(credentials.credentials,
                           expected_type=TokenType.ACCESS)

    user = await get_user_by_id_or_none(user_id=int(payload["sub"]))

    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user
