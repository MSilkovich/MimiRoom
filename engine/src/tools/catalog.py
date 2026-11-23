"""Каталог услуг и мастеров как кешируемый документ для LLM.

Идея: список услуг/мастеров меняется редко, поэтому формируем компактный
документ из core (`/s/services` + `/s/masters`) и кешируем его на TTL.
В контекст модели документ подставляется как system-сообщение, чтобы у неё
всегда были актуальные названия, id, цены, длительность и мастера.

Источник правды — только core. Здесь нет собственных списков услуг.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any

from src.logging import get_logger
from src.repositories import backend_repository

logger = get_logger(__name__)

CATALOG_TTL_SEC = int(os.getenv("CATALOG_TTL_SEC", "1800"))
DEFAULT_SERVICE_KEYWORDS = ("комплекс", "полный", "груминг")


# ---------------------------------------------------------------------------
# Нормализация и нечёткое сопоставление
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Привести строку к сравнимому виду (регистр, ё, пунктуация, пробелы)."""
    lowered = (text or "").strip().lower().replace("ё", "е")
    cleaned = []
    for ch in lowered:
        if ch.isalnum() or ch.isspace():
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    return " ".join("".join(cleaned).split())


def match_score(query: str, title: str) -> float:
    """Похожесть запроса на название (учитывая отдельные слова названия)."""
    q = normalize(query)
    t = normalize(title)
    if not q or not t:
        return 0.0
    if q == t:
        return 1.0
    if len(q) >= 3 and (q in t or t in q):
        return 0.95
    full = SequenceMatcher(None, q, t).ratio()
    tokens = t.split()
    token_best = max(
        (SequenceMatcher(None, q, token).ratio() for token in tokens),
        default=0.0,
    )
    return max(full, token_best)


# ---------------------------------------------------------------------------
# Проекции (компактные карточки — единый формат во всех выводах)
# ---------------------------------------------------------------------------

def _full_name(person: dict[str, Any]) -> str:
    parts = [person.get("name"), person.get("surname")]
    return " ".join(p for p in parts if p) or str(person.get("user_id"))


def project_service(service: dict[str, Any]) -> dict[str, Any]:
    """Компактная карточка услуги для модели."""
    return {
        "service_id": service.get("service_id"),
        "title": service.get("title"),
        "price": service.get("price"),
        "duration_minutes": service.get("duration_minutes"),
        "breed": service.get("breed_title"),
        "masters": [
            {
                "user_id": master.get("user_id"),
                "name": _full_name(master),
            }
            for master in (service.get("masters") or [])
        ],
    }


def project_master(master: dict[str, Any]) -> dict[str, Any]:
    """Компактная карточка мастера для модели."""
    return {
        "user_id": master.get("user_id"),
        "name": _full_name(master),
        "services": [
            {
                "service_id": service.get("service_id"),
                "title": service.get("title"),
            }
            for service in (master.get("services") or [])
        ],
    }


def build_catalog(
    services: list[dict[str, Any]], masters: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "services": [project_service(s) for s in (services or [])],
        "masters": [project_master(m) for m in (masters or [])],
    }


# ---------------------------------------------------------------------------
# Кеш
# ---------------------------------------------------------------------------

_cache: dict[str, Any] | None = None
_cache_at: float = 0.0


def invalidate_cache() -> None:
    """Сбросить кеш каталога (используется в тестах и при ручном refresh)."""
    global _cache, _cache_at
    _cache = None
    _cache_at = 0.0


async def get_catalog(force: bool = False) -> dict[str, Any]:
    """Вернуть каталог (из кеша или пересобрав по TTL)."""
    global _cache, _cache_at
    fresh = _cache is not None and (time.monotonic() - _cache_at) < CATALOG_TTL_SEC
    if fresh and not force:
        return _cache  # type: ignore[return-value]

    services = await backend_repository.get_services(limit=500, offset=0)
    masters = await backend_repository.get_masters(limit=500, offset=0)
    _cache = build_catalog(services or [], masters or [])
    _cache_at = time.monotonic()
    logger.info(
        "Catalog refreshed: services=%d masters=%d ttl=%ds",
        len(_cache["services"]), len(_cache["masters"]), CATALOG_TTL_SEC,
    )
    return _cache


# ---------------------------------------------------------------------------
# Поиск
# ---------------------------------------------------------------------------

def find_services(
    query: str,
    catalog: dict[str, Any],
    limit: int = 5,
    min_score: float = 0.55,
) -> list[dict[str, Any]]:
    """Найти услуги по нечёткому запросу (возвращает карточки + score)."""
    scored: list[tuple[float, dict[str, Any]]] = []
    for card in catalog.get("services", []):
        score = match_score(query, card.get("title") or "")
        if score >= min_score:
            scored.append((score, card))
    scored.sort(key=lambda item: item[0], reverse=True)
    result: list[dict[str, Any]] = []
    for score, card in scored[:limit]:
        enriched = dict(card)
        enriched["score"] = round(score, 2)
        result.append(enriched)
    return result


def find_default_service(
    catalog: dict[str, Any], keywords: tuple[str, ...] = DEFAULT_SERVICE_KEYWORDS
) -> dict[str, Any] | None:
    """Найти «дефолтную» общую услугу (напр. комплексный груминг) при 0 совпадений."""
    services = catalog.get("services", [])
    for keyword in keywords:
        key = normalize(keyword)
        for card in services:
            if key in normalize(card.get("title") or ""):
                return card
    return None


# ---------------------------------------------------------------------------
# Рендер документа в контекст
# ---------------------------------------------------------------------------

def render_catalog_block(
    catalog: dict[str, Any], max_services: int = 40
) -> str:
    """Отрендерить компактный документ каталога для system-сообщения."""
    services = catalog.get("services", [])
    masters = catalog.get("masters", [])

    lines: list[str] = [
        f"КАТАЛОГ САЛОНА (данные на {catalog.get('generated_at', '')}; "
        "используй ТОЛЬКО эти id и названия, не выдумывай):",
        "УСЛУГИ:",
    ]
    for card in services[:max_services]:
        masters_str = ", ".join(
            f"id={m['user_id']} {m['name']}" for m in card.get("masters", [])
        ) or "нет"
        breed = card.get("breed")
        breed_str = f" | размер/порода: {breed}" if breed else ""
        lines.append(
            f"- id={card['service_id']} | {card['title']} | "
            f"{card['price']} ₽ | {card.get('duration_minutes')} мин"
            f"{breed_str} | мастера: {masters_str}"
        )
    if len(services) > max_services:
        lines.append(
            f"… и ещё {len(services) - max_services} услуг. "
            "Для поиска нужной услуги вызови find_service."
        )

    if masters:
        lines.append("МАСТЕРА:")
        for master in masters:
            svc_ids = ", ".join(
                str(s["service_id"]) for s in master.get("services", [])
            ) or "нет"
            lines.append(
                f"- id={master['user_id']} | {master['name']} | услуги: {svc_ids}"
            )
    return "\n".join(lines)


def catalog_maps(
    catalog: dict[str, Any],
) -> tuple[dict[int, dict], dict[int, dict]]:
    """Словари service_id→card и user_id→card для обогащения ответов."""
    services = {
        card["service_id"]: card
        for card in catalog.get("services", [])
        if card.get("service_id") is not None
    }
    masters = {
        card["user_id"]: card
        for card in catalog.get("masters", [])
        if card.get("user_id") is not None
    }
    return services, masters
