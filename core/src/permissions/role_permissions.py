from .bitmask import grant
from .enums.permissions import Permission as P
from .enums.scope import Scope


def _admin() -> int:
    m = 0
    for p in P:
        m = grant(m, p, scope=Scope.ALL)
    return m


# TODO: вручную перелопатить
ROLE_MASK: dict[str, int] = {
    "admin": _admin(),

    "manager": grant(
        0,
        P.USER_READ,
        P.BREED_READ, P.BREED_WRITE,
        P.SERVICE_READ, P.SERVICE_WRITE, P.SERVICE_DELETE,
        P.STORAGE_READ, P.STORAGE_WRITE,
        P.SERVICE_CONSUMABLE_WRITE,
        P.BOOK_READ, P.BOOK_WRITE, P.BOOK_CANCEL,
        P.PET_READ, P.PET_WRITE,
        scope=Scope.ALL,
    ),

    # ваш пример: читаем всех питомцев и записи, меняем только своих
    "groomer": grant(
        grant(
            0,
            P.BREED_READ, P.SERVICE_READ, P.STORAGE_READ,
            P.PET_READ, P.BOOK_READ,
            scope=Scope.ALL,
        ),
        P.PET_WRITE, P.BOOK_WRITE, P.BOOK_CANCEL,
        scope=Scope.OWN,
    ),

    # ваш пример: всё со своими, чужие даже не читаем
    "client": grant(
        0,
        P.BREED_READ, P.SERVICE_READ,
        P.PET_READ, P.PET_WRITE, P.PET_DELETE,
        P.BOOK_READ, P.BOOK_WRITE, P.BOOK_CANCEL,
        scope=Scope.OWN,
    ),
}
