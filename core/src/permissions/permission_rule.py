from dataclasses import dataclass
from sqlalchemy import true, Column

from .enums.permissions import Permission
from .enums.scope import Scope


@dataclass(frozen=True)
class PermissionRule:
    """Результат проверки права: что можно и в каких рамках."""
    permission: Permission
    scope: Scope
    # если OWN — фильтр по владельцу; если ALL — None
    owner_id: int | None
    # Имя колонки, по которой ограничивается OWN-доступ. Для большинства
    # сущностей это аудит who_create, но у питомцев — owner_id, у броней —
    # client_id/master_id, у графиков — master_id.
    owner_field: str = "who_create"

    @property
    def is_unrestricted(self) -> bool:
        return self.owner_id is None

    def allows_owner(self, user_id: int | None) -> bool:
        if self.is_unrestricted:
            return True
        return user_id is not None and user_id == self.owner_id

    def sql_filter(self, column: Column):
        if self.is_unrestricted:
            return true()
        return column == self.owner_id
