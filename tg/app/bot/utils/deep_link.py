"""Разбор payload deep-link команды ``/start``.

Привязка внешнего провайдера к аккаунту выполняется **только** одноразовым
кодом (core: ``POST /users/link/code`` + ``POST /users/link/code/consume``).
Поэтому payload ссылки ``https://t.me/<bot>?start=<code>`` — это сам код,
а не access-токен и не набор полей.

Telegram ограничивает payload: 1–64 символа, алфавит ``A-Z a-z 0-9 _ -``.
Core генерирует код из ``A-Z a-z 0-9``, поэтому принимаем только его.
"""

from __future__ import annotations

import re

# Код core: LINK_CODE_LENGTH символов из string.ascii_letters + string.digits.
# Верхняя граница 64 — ограничение Telegram на payload deep-link.
_CODE_RE = re.compile(r"^[A-Za-z0-9]{1,64}$")


def parse_start_code(raw: str | None) -> str | None:
    """Вернуть одноразовый код из payload ``/start`` или ``None``."""
    if not raw:
        return None

    code = raw.strip()
    if not _CODE_RE.fullmatch(code):
        return None

    return code
