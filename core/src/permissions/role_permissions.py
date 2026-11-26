from .bitmask import grant
from .enums.permissions import Permission as P
from .enums.scope import Scope
from .enums.roles import Role


def _admin() -> int:
    m = 0
    for p in P:
        m = grant(m, p, scope=Scope.ALL)
    return m


ROLE_MASK: dict[Role, int] = {
    Role.ADMIN: _admin(),

    # менеджер: весь бизнес-контур, пользователи только читаются
    Role.MANAGER: grant(
        grant(
            0,
            # пользователи: читать всех
            P.USER_READ,
            # справочники: читать + вести, но не удалять
            P.DICTIONARIES_READ, P.DICTIONARIES_WRITE,
            # услуги: полный цикл
            P.SERVICE_READ, P.SERVICE_WRITE, P.SERVICE_DELETE,
            # мастера: читать + вести (удаление профиля — только админ)
            P.MASTER_READ, P.MASTER_WRITE,
            # график: полный цикл
            P.SCHEDULE_READ, P.SCHEDULE_WRITE, P.SCHEDULE_DELETE,
            # склад: читать + вести, но не удалять
            P.STORAGE_READ, P.STORAGE_WRITE,
            # брони: читать/создавать/отменять любые (жёсткое удаление — админ)
            P.BOOK_READ, P.BOOK_WRITE, P.BOOK_CANCEL,
            # питомцы: читать/править любых (удаление — админ/клиент)
            P.PET_READ, P.PET_WRITE,
            scope=Scope.ALL,
        ),
        # свой профиль (ЛК) — править и удалять только себя
        P.USER_WRITE, P.USER_DELETE,
        scope=Scope.OWN,
    ),

    # грумер: видит всех питомцев и мастеров, работает только со своими записями
    Role.GROOMER: grant(
        grant(
            0,
            # справочники/каталог/склад — только читать, зато всё
            P.DICTIONARIES_READ,
            P.SERVICE_READ,
            P.STORAGE_READ,
            # питомцев видит всех (нужно перед стрижкой)
            P.PET_READ,
            # коллег-мастеров видит (публичный каталог)
            P.MASTER_READ,
            scope=Scope.ALL,
        ),
        # со своими записями и своими питомцами — полный цикл
        P.BOOK_READ, P.BOOK_WRITE, P.BOOK_CANCEL,
        P.PET_WRITE,
        # свой график — только чтение
        P.SCHEDULE_READ,
        # свой профиль и свой профиль мастера — править
        P.USER_READ, P.USER_WRITE, P.USER_DELETE,
        P.MASTER_WRITE,
        scope=Scope.OWN,
    ),

    # клиент: только своё, справочники и каталог — читать
    Role.CLIENT: grant(
        grant(
            0,
            P.DICTIONARIES_READ,
            P.SERVICE_READ,
            P.MASTER_READ,
            scope=Scope.ALL,
        ),
        P.PET_READ, P.PET_WRITE, P.PET_DELETE,
        P.BOOK_READ, P.BOOK_WRITE, P.BOOK_CANCEL,
        P.USER_READ, P.USER_WRITE, P.USER_DELETE,
        scope=Scope.OWN,
    ),
}
