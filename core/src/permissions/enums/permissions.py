from enum import IntEnum


class Permission(IntEnum):
    """
    NOTE: это НЕ значение бита, а НОМЕР СЛОТА (0, 1, 2, ...).
    Реальный сдвиг в маске = index * 2 (2 bit на слот)
    Правило: номера только растут. Удалённый — «надгробие» (_RESERVED_...), не переиспользуем. Это гарантирует стабильность уже сохранённых масок в БД.
    """

    USER_READ = 0
    USER_WRITE = 1
    USER_DELETE = 2

    BREED_READ = 3
    BREED_WRITE = 4
    BREED_DELETE = 5

    SERVICE_READ = 6
    SERVICE_WRITE = 7
    SERVICE_DELETE = 8

    STORAGE_READ = 9
    STORAGE_WRITE = 10
    STORAGE_DELETE = 11

    BOOK_READ = 12
    BOOK_WRITE = 13
    BOOK_CANCEL = 14
    BOOK_DELETE = 15

    PET_READ = 16
    PET_WRITE = 17
    PET_DELETE = 18
