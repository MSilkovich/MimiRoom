from typing import Any

from pydantic import Field

from src.models.enums.provider import Provider

from .base_schema import Base


class UserLinkRead(Base):
    """Привязка внешнего провайдера к пользователю core."""

    id: int
    user_id: int
    provider: Provider
    external_id: str = Field(..., max_length=64)
    options: dict[str, Any] = Field(default_factory=dict)


class UserLinkCreate(Base):
    # Для пользовательских запросов user_id подставляет сервер (из access-токена).
    # Для сервисных запросов user_id обязателен.
    user_id: int | None = Field(default=None, examples=[1])
    provider: Provider
    external_id: str = Field(..., max_length=64, examples=["123456789"])
    options: dict[str, Any] = Field(default_factory=dict)


class UserLinkUpdate(Base):
    """Частичное обновление привязки (все поля опциональны)."""

    provider: Provider | None = None
    external_id: str | None = Field(default=None, max_length=64)
    options: dict[str, Any] | None = None


class LinkCodeResponse(Base):
    """Одноразовый код для deep-link привязки Telegram."""

    code: str = Field(..., examples=["A1b2C3d4E5f6"])
    expires_in: int = Field(..., examples=[300], description="TTL кода, секунды")
    deep_link: str | None = Field(
        default=None, examples=["https://t.me/MyBot?start=A1b2C3d4E5f6"]
    )


class LinkCodeConsumeRequest(Base):
    """Обмен одноразового кода на привязку (вызывает сервис-бот)."""

    code: str = Field(..., min_length=1, max_length=64)
    provider: Provider = Field(default=Provider.TELEGRAM)
    external_id: str = Field(..., max_length=64, examples=["123456789"])
    options: dict[str, Any] = Field(default_factory=dict)
