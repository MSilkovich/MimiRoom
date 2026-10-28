from .enums.permissions import Permission
from .enums.scope import Scope


SCOPE_BITS = 2
SCOPE_MASK = 0b11


def _shift(perm: Permission) -> int:
    return int(perm) * SCOPE_BITS


def get_scope(mark: int, perm: Permission) -> Scope:
    """Достать scope для одной операции."""
    return Scope((mark >> _shift(perm)) & SCOPE_MASK)


def set_scope(mark: int, perm: Permission, scope: Scope) -> int:
    """Записать scope, не трогая остальные операции."""
    shift = _shift(perm)
    return (mark & ~(SCOPE_MASK << shift)) | (int(scope) << shift)


def grant(mark: int, *perms: Permission, scope: Scope = Scope.OWN) -> int:
    for p in perms:
        mark = set_scope(mark, p, scope)
    return mark


def revoke(mark: int, *perms: Permission) -> int:
    for p in perms:
        mark = set_scope(mark, p, Scope.NONE)
    return mark


def has(mark: int, perm: Permission, required: Scope = Scope.OWN) -> bool:
    return get_scope(mark, perm).allows(required)


def to_dict(mark: int) -> dict[str, str]:
    """Единственная точка расшифровки: перебор всех Permission."""
    return {
        p.name: get_scope(mark, p).name
        for p in Permission
        if get_scope(mark, p) != Scope.NONE
    }


def validate_permissions() -> None:
    """Проврека что в системе не более 32 разрешений"""
    indices = [int(p) for p in Permission]
    assert len(indices) == len(set(indices)), "Duplicate permission index"
    max_slot = max(indices)
    assert max_slot * SCOPE_BITS + SCOPE_BITS <= 63, \
        f"Too many permissions for BIGINT: max slot {max_slot}"
