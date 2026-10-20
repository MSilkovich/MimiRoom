from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from src.models import TokenType, User
from src.context import set_current_user, current_user
from config.jwt.jwt_config import settings_jwt
from src.models.user import User


bearer_scheme = HTTPBearer(auto_error=False)


def _create_token(sub: str, token_type: str, expires: timedelta, jti: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": sub,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires).timestamp()),
    }
    if jti:
        payload["jti"] = jti
    return jwt.encode(payload, settings_jwt.JWT_SECRET_KEY, algorithm=settings_jwt.JWT_ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _create_token(
        sub=str(user_id),
        token_type=TokenType.ACCESS,
        expires=timedelta(
            minutes=settings_jwt.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: int, jti: str) -> str:
    return _create_token(
        sub=str(user_id),
        token_type=TokenType.REFRESH,
        expires=timedelta(days=settings_jwt.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        jti=jti,
    )


def decode_token(token: str, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(token, settings_jwt.JWT_SECRET_KEY, algorithms=[
                             settings_jwt.JWT_ALGORITHM])
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            f"Invalid token: {e}")
    if expected_type and payload.get("type") != expected_type:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            f"Expected {expected_type} token")
    return payload


# ---------- Мидлварь: положить User в ContextVar ----------

class AuthMiddleware(BaseHTTPMiddleware):
    """На каждый запрос: если есть Bearer — достаёт User и кладёт в ContextVar.

    НЕ падает, если токена нет или он кривой — это забота конкретных роутов.
    """

    async def dispatch(self, request: Request, call_next):
        from src.dependencies import get_uow_factory
        from src.models.user import User

        header = request.headers.get("Authorization", "")
        user = None

        if header.lower().startswith("bearer "):
            token = header.split(" ", 1)[1].strip()
            try:
                payload = decode_token(token, expected_type=TokenType.ACCESS)
                user_id = int(payload["sub"])

                async with get_uow_factory()() as uow:
                    repo = uow.repository(User)
                    user = await repo.get_single(user_id=user_id)
            except Exception:
                user = None

        token_ctx = set_current_user(user)
        try:
            response = await call_next(request)
        finally:
            current_user.reset(token_ctx)
        return response


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    payload = decode_token(credentials.credentials,
                           expected_type=TokenType.ACCESS)

    from src.dependencies import get_uow_factory
    async with get_uow_factory()() as uow:
        user = await uow.users.get_single(user_id=int(payload["sub"]))
        await uow.rollback()

    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user
