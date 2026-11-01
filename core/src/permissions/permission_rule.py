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
    def is_unrestricted(self) -> bool:
        return self.owner_id is None

    def allows_owner(self, user_id: int | None) -> bool:
        if self.is_unrestricted:
            return True
        return user_id is not None and user_id == self.owner_id

    def sql_filter(self, column):
        if self.is_unrestricted:
            return None
        return column == self.owner_id
