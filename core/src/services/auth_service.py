from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from config.jwt import settings_jwt
from src.models import User, TokenType
from src.excpetions.auth import InvalidCredentialsError, InvalidTokenError, UserAlreadyExistsError
from src.context import system_context
from src.schemas.auth.auth import RegisterRequest
from src.services.generic_service import UowFactory

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, uow_factory: UowFactory) -> None:
        self.uow_factory = uow_factory

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @staticmethod
    def _create_token(sub: str, token_type: str, expires_delta: timedelta, jti: str | None = None) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(sub),
            "type": token_type,
            "iat": int(now.timestamp()),
            "exp": int((now + expires_delta).timestamp()),
        }
        if jti is not None:
            payload["jti"] = jti
        return jwt.encode(payload, settings_jwt.JWT_SECRET_KEY, algorithm=settings_jwt.JWT_ALGORITHM)

    @classmethod
    def create_access_token(cls, user_id: int | str) -> str:
        return cls._create_token(
            sub=str(user_id),
            token_type=TokenType.ACCESS,
            expires_delta=timedelta(
                minutes=settings_jwt.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        )

    @classmethod
    def create_refresh_token(cls, user_id: int | str, jti: str) -> str:
        return cls._create_token(
            sub=str(user_id),
            token_type=TokenType.REFRESH,
            expires_delta=timedelta(
                days=settings_jwt.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
            jti=jti,
        )

    @staticmethod
    def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, settings_jwt.JWT_SECRET_KEY, algorithms=[
                                 settings_jwt.JWT_ALGORITHM])
        except JWTError as e:
            raise InvalidTokenError(str(e)) from e
        if expected_type and payload.get("type") != expected_type:
            raise InvalidTokenError(f"expected {expected_type}")
        if "sub" not in payload:
            raise InvalidTokenError("missing sub")
        return payload

    # region auth methods

    async def register(self, requst: RegisterRequest) -> User:
        with system_context():
            async with self.uow_factory() as uow:
                if await uow.users.get_single(login=requst.login):
                    raise UserAlreadyExistsError()
                requst.password = self.hash_password(requst.password)
                # TODO: role ставить client тк на регистрацию нельзя привиллегии давать
                user = await uow.users.create(requst.model_dump())
                await uow.commit()
        return user

    async def authenticate(self, login: str, password: str) -> int:
        async with self.uow_factory() as uow:
            repo = uow.repository(User)
            user = await repo.get_single(login=login)

        if user is None or not self.verify_password(password, user.password):
            raise InvalidCredentialsError("Invalid login or password")
        return user.user_id

    async def issue_pair(self, user_id: int) -> dict[str, Any]:
        """Создать access+refresh, refresh сохранить в БД."""
        jti = str(uuid.uuid4())
        access = self.create_access_token(user_id)
        refresh = self.create_refresh_token(user_id, jti)
        with system_context():
            async with self.uow_factory() as uow:
                await uow.refresh_tokens.create({
                    "jti": jti,
                    "user_id": user_id,
                    "expires_at": datetime.now(timezone.utc) + timedelta(days=settings_jwt.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
                    "revoked": False,
                })
                await uow.commit()

        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": settings_jwt.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_id": user_id,
        }

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        """Проверить подпись + наличие jti в БД + не revoked + не expired.

        Ротация: старый refresh помечаем revoked, выдаём новую пару.
        """
        payload = self.decode_token(
            refresh_token, expected_type=TokenType.REFRESH)
        jti = payload["jti"]
        with system_context():
            async with self.uow_factory() as uow:
                stored = await uow.refresh_tokens.get_by_jti(jti)
                if not stored or stored.revoked:
                    raise InvalidTokenError("revoked")
                if stored.expires_at < datetime.now(timezone.utc):
                    raise InvalidTokenError("expired")
                await uow.refresh_tokens.revoke(jti)
                await uow.commit()
        return await self.issue_pair(int(payload["sub"]))

    async def logout(self, refresh_token: str) -> None:
        """Отозвать конкретный refresh."""
        try:
            payload = self.decode_token(refresh_token, expected_type="refresh")
        except InvalidTokenError:
            return
        jti = payload.get("jti")
        if not jti:
            return
        with system_context():
            async with self.uow_factory() as uow:
                await uow.refresh_tokens.revoke(jti)
                await uow.commit()

    async def logout_all(self, user_id: int) -> None:
        with system_context():
            async with self.uow_factory() as uow:
                await uow.refresh_tokens.revoke_all_for_user(user_id)
            await uow.commit()
