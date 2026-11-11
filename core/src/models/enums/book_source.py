from enum import Enum


class BookSource(str, Enum):
    WEBSITE = "website"
    PHONE = "phone"
    BOT = "bot"
    WALK_IN = "walk_in"
