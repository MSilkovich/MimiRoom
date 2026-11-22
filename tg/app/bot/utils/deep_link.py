"""Разбор deep-link payload команды ``/start``.

Telegram отдаёт payload из ``https://t.me/<bot>?start=<PAYLOAD>`` в
``CommandObject.args``. Ограничения Telegram: 1–64 символа, алфавит
``A-Z a-z 0-9 _ -``. Поэтому «как есть» строку ``user_id=1&token=...``
передать нельзя — поддерживаем несколько форматов:

1. JSON: ``{"user_id": 1, "token": "..."}`` (обычно в base64url).
2. Query: ``user_id=1&token=...`` (обычно в base64url).
3. Компактно: ``1:token`` / ``1_token`` / ``1-token``.
4. Опаковый код: ``<code>`` — трактуем как token без user_id.

Для продакшена рекомендуется вариант «короткий одноразовый код»: ссылка
``?start=<code>``, а core по коду сам находит пользователя.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote


@dataclass(frozen=True)
class LinkPayload:
    user_id: int | None
    token: str | None
    raw: str


def _try_b64decode(value: str) -> str | None:
    try:
        padded = value + "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(padded).decode("utf-8")
    except Exception:  # noqa: BLE001 — payload произвольный
        return None


def _parse_json_or_query(value: str) -> tuple[int | None, str | None] | None:
    value = value.strip()
    if not value:
        return None

    if value.startswith("{"):
        try:
            obj = json.loads(value)
        except json.JSONDecodeError:
            pass
        else:
            uid = obj.get("user_id", obj.get("uid"))
            token = obj.get("token", obj.get("t"))
            try:
                user_id = int(uid) if uid is not None else None
            except (TypeError, ValueError):
                user_id = None
            return user_id, token

    if "=" in value:
        parsed = parse_qs(value)
        if any(k in parsed for k in ("user_id", "uid", "token", "t")):
            uid = (parsed.get("user_id") or parsed.get("uid") or [None])[0]
            token = (parsed.get("token") or parsed.get("t") or [None])[0]
            try:
                user_id = int(uid) if uid is not None else None
            except (TypeError, ValueError):
                user_id = None
            return user_id, token

    return None


def parse_start_payload(raw: str | None) -> LinkPayload:
    """Разобрать payload /start в :class:`LinkPayload`."""
    if not raw:
        return LinkPayload(None, None, "")

    raw = raw.strip()
    candidates: list[str] = [raw]

    unquoted = unquote(raw)
    if unquoted != raw:
        candidates.append(unquoted)

    for candidate in list(candidates):
        decoded = _try_b64decode(candidate)
        if decoded and decoded not in candidates:
            candidates.append(decoded)

    for candidate in candidates:
        parsed = _parse_json_or_query(candidate)
        if parsed and (parsed[0] is not None or parsed[1]):
            return LinkPayload(parsed[0], parsed[1], raw)

    # Компактный вид: user_id:token / user_id_token / user_id-token
    for sep in (":", "_", "-"):
        if raw.count(sep) == 1:
            head, tail = raw.split(sep, 1)
            if head.isdigit():
                return LinkPayload(int(head), tail or None, raw)

    # Опаковый код — единственный «токен».
    return LinkPayload(None, raw, raw)
