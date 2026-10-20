from pydantic import Field

from src.schemas.base_schema import Base
from src.models import TokenType


class RegisterRequest(Base):
    login: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class TokenRequest(Base):
    username: str
    password: str
    grant_type: str = "password"


class RefreshRequest(Base):
    refresh_token: str
    grant_type: str = TokenType.REFRESH


class LogoutRequest(Base):
    refresh_token: str


class TokenResponse(Base):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int


class UserMeResponse(Base):
    user_id: int
