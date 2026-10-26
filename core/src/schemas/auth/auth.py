from pydantic import Field

from src.schemas.base_schema import Base
from src.models import TokenType


class RegisterRequest(Base):
    login: str = Field(min_length=3, max_length=64, examples=["john_doe"])
    password: str = Field(
        min_length=6,
        max_length=128,
        examples=["secret123"],
        description="Пароль, 6–128 символов",
    )
    name: str = Field(min_length=2, max_length=255, examples=["Иван"])
    surname: str = Field(min_length=2, max_length=255, examples=["Иванов"])
    patronymic: str | None = Field(
        default=None,
        min_length=6,
        max_length=255,
        examples=["Иванович"],
        description="Отчество. Необязательно, но если передано — от 6 символов.",
    )


class TokenRequest(Base):
    username: str = Field(..., examples=["john_doe"])
    password: str = Field(..., examples=["secret123"])
    grant_type: str = Field(default="password", examples=["password"])


class RefreshRequest(Base):
    refresh_token: str = Field(..., examples=["eyJhbGciOiJIUzI1NiIs..."])
    grant_type: str = Field(default=TokenType.REFRESH, examples=["refresh"])


class LogoutRequest(Base):
    refresh_token: str = Field(..., examples=["eyJhbGciOiJIUzI1NiIs..."])


class TokenResponse(Base):
    access_token: str = Field(..., examples=["eyJhbGciOiJIUzI1NiIs..."])
    refresh_token: str = Field(..., examples=["eyJhbGciOiJIUzI1NiIs..."])
    token_type: str = Field(default="bearer", examples=["bearer"])
    expires_in: int = Field(..., examples=[
                            3600], description="Время жизни access_token, секунды")
    user_id: int = Field(..., examples=[1])


class UserMeResponse(Base):
    user_id: int = Field(..., examples=[1])
