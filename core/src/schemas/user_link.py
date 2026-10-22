from typing import Any

from pydantic import Field

from src.models.enums.provider import Provider

from .base_schema import Base


class UserLinkRead(Base):
    provider: Provider
    external_id: str = Field(..., max_length=64)
    options: dict[str, Any] = Field(default_factory=dict)


class UserLinkCreate(Base):
    user_id: int
    provider: Provider
    external_id: str = Field(..., max_length=64)
    options: dict[str, Any] = Field(default_factory=dict)


class UserLinkUpdate(Base):
    provider: Provider
    external_id: str = Field(..., max_length=64)
    options: dict[str, Any] = Field(default_factory=dict)
