from decimal import Decimal

from pydantic import Field

from .base_schema import Base


class ServiceBriefRead(Base):
    """Краткое представление услуги внутри карточки мастера."""

    service_id: int
    title: str
    duration_minutes: int | None
    price: Decimal
    is_active: bool


class ResourceBriefRead(Base):
    """Краткое представление мастера (используется в услугах)."""

    resource_id: int
    title: str
    is_active: bool


class ResourceRead(Base):
    resource_id: int
    title: str
    description: str | None
    is_active: bool
    organization_id: int | None
    services: list[ServiceBriefRead] = Field(default_factory=list)

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "resource_id": 1,
                "title": "Анна",
                "description": "Груминг кошек и небольших собак",
                "is_active": True,
                "organization_id": None,
                "services": [
                    {
                        "service_id": 3,
                        "title": "Стрижка кошки",
                        "duration_minutes": 60,
                        "price": "1500.00",
                        "is_active": True,
                    }
                ],
            },
        },
    }


class ResourceCreate(Base):
    title: str = Field(..., examples=["Анна"])
    description: str | None = Field(
        default=None, examples=["Груминг кошек и небольших собак"]
    )
    is_active: bool = Field(default=True, examples=[True])
    organization_id: int | None = Field(default=None, examples=[None])
    service_ids: list[int] = Field(
        default_factory=list,
        description="Услуги, которые оказывает мастер",
        examples=[[3, 4]],
    )


class ResourceUpdate(Base):
    title: str | None = Field(default=None, examples=["Анна"])
    description: str | None = Field(default=None)
    is_active: bool | None = Field(default=None, examples=[True])
    organization_id: int | None = Field(default=None)
    service_ids: list[int] | None = Field(
        default=None, description="Если передано — набор услуг будет заменён"
    )
