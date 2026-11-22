from decimal import Decimal

from pydantic import Field

from .base_schema import Base


class ServiceBriefRead(Base):
    """Краткое представление услуги внутри карточки мастера."""

    service_id: int
    title: str
    duration_minutes: int | None
    price: Decimal


class MasterBriefRead(Base):
    """Краткое представление мастера (используется в услугах)."""

    user_id: int
    name: str
    surname: str
    role: str


class MasterRead(Base):
    user_id: int
    login: str
    name: str
    surname: str
    patronymic: str | None
    phone: str | None
    email: str | None
    role: str
    services: list[ServiceBriefRead] = Field(default_factory=list)

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "login": "anna",
                "name": "Анна",
                "surname": "Иванова",
                "patronymic": None,
                "phone": "+79990001122",
                "email": None,
                "role": "groomer",
                "services": [
                    {
                        "service_id": 3,
                        "title": "Стрижка кошки",
                        "duration_minutes": 60,
                        "price": "1500.00",
                    }
                ],
            },
        },
    }


class MasterCreate(Base):
    """Создать мастера = создать пользователя с ролью groomer."""

    login: str = Field(..., examples=["anna"])
    password: str = Field(..., examples=["secret"])
    name: str = Field(..., examples=["Анна"])
    surname: str = Field(..., examples=["Иванова"])
    patronymic: str | None = Field(default=None)
    phone: str | None = Field(default=None, examples=["+79990001122"])
    email: str | None = Field(default=None)
    service_ids: list[int] = Field(
        default_factory=list,
        description="Услуги, которые оказывает мастер",
        examples=[[3, 4]],
    )


class MasterUpdate(Base):
    login: str | None = Field(default=None)
    password: str | None = Field(default=None)
    name: str | None = Field(default=None)
    surname: str | None = Field(default=None)
    patronymic: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    email: str | None = Field(default=None)
    service_ids: list[int] | None = Field(
        default=None, description="Если передано — набор услуг будет заменён"
    )
