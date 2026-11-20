from dataclasses import dataclass
from enum import Enum
from src.models import User


class PrincipalKind(str, Enum):
    USER = "user"
    SERVICE = "service"


@dataclass(frozen=True)
class Principal:
    kind: PrincipalKind
    user: User | None = None
    service_payload: dict | None = None

    @property
    def is_user(self) -> bool:
        return self.kind is PrincipalKind.USER

    @property
    def is_service(self) -> bool:
        return self.kind is PrincipalKind.SERVICE
