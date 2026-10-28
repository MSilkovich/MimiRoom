from enum import IntEnum


class Scope(IntEnum):
    NONE = 0b00
    OWN = 0b01
    ALL = 0b10
    # 0b11 свободно (можно потом использовать)

    def allows(self, required: "Scope") -> bool:
        return self >= required
