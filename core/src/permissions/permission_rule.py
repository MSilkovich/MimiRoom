from dataclasses import dataclass

from .enums.permissions import Permission
from .enums.scope import Scope


@dataclass(frozen=True)
class PermissionRule:
    """Результат проверки права: что можно и в каких рамках."""
    permission: Permission
    scope: Scope
    # если OWN — фильтр по владельцу; если ALL — None
    owner_id: int | None

    @property
    def unrestricted(self) -> bool:
        return self.owner_id is None

    def allows_owner(self, owner_id: int | None) -> bool:
        if self.unrestricted:
            return True
        return owner_id is not None and owner_id == self.owner_id

    def sql_filter(self, column):
        if self.unrestricted:
            return None
        return column == self.owner_id
