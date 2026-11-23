"""Резолвинг ссылок на услугу/мастера: id ИЛИ человекочитаемое имя.

Детерминированные правила (без «угадывания»):
- int → ищем по id;
- str → нормализуем; точное совпадение названия; иначе нечёткий поиск;
  - один явный лидер → ок;
  - несколько близких → ``ambiguous`` (нужно уточнение у пользователя);
  - ничего похожего → ``not_found`` с подсказками.

Возвращаемый результат — dict:
``{"status": "ok", "service"| "master": card}``
``{"status": "ambiguous", "candidates": [...]}``
``{"status": "not_found", "candidates": [...]}``
"""

from __future__ import annotations

from typing import Any

from . import catalog as catalog_mod

# Порог «уверенного» лидера и минимальный отрыв от второго кандидата.
_CONFIDENT_SCORE = 0.85
_CONFIDENT_MARGIN = 0.12


def _as_int(ref: Any) -> int | None:
    if isinstance(ref, bool):
        return None
    if isinstance(ref, int):
        return ref
    if isinstance(ref, str) and ref.strip().isdigit():
        return int(ref.strip())
    return None


def _services_map(catalog: dict[str, Any]) -> dict[int, dict]:
    return catalog_mod.catalog_maps(catalog)[0]


def _masters_map(catalog: dict[str, Any]) -> dict[int, dict]:
    return catalog_mod.catalog_maps(catalog)[1]


def resolve_service(ref: Any, catalog: dict[str, Any]) -> dict[str, Any]:
    """Разрешить ссылку на услугу (id или название) в карточку услуги."""
    if ref is None or (isinstance(ref, str) and not ref.strip()):
        return {"status": "not_found", "candidates": []}

    as_int = _as_int(ref)
    if as_int is not None:
        card = _services_map(catalog).get(as_int)
        if card is None:
            return {
                "status": "not_found",
                "candidates": catalog.get("services", [])[:3],
            }
        return {"status": "ok", "service": card}

    query = str(ref)
    candidates = catalog_mod.find_services(query, catalog, limit=5)
    if not candidates:
        return {
            "status": "not_found",
            "candidates": catalog_mod.find_services(
                query, catalog, limit=3, min_score=0.3
            ),
        }

    top = candidates[0]
    if len(candidates) == 1:
        return {"status": "ok", "service": top}
    second = candidates[1]
    if (
        top["score"] >= _CONFIDENT_SCORE
        and (top["score"] - second["score"]) >= _CONFIDENT_MARGIN
    ):
        return {"status": "ok", "service": top}
    return {"status": "ambiguous", "candidates": candidates[:3]}


def resolve_master(
    ref: Any,
    catalog: dict[str, Any],
    service_id: int | None = None,
) -> dict[str, Any]:
    """Разрешить ссылку на мастера (id или имя), опционально в рамках услуги."""
    if ref is None or (isinstance(ref, str) and not ref.strip()):
        return {"status": "not_found", "candidates": []}

    all_masters = catalog.get("masters", [])
    if service_id is not None:
        scoped = [
            m
            for m in all_masters
            if any(s.get("service_id") == service_id for s in m.get("services", []))
        ]
        # Если у услуги нет явного списка мастеров — не сужаем.
        pool = scoped or all_masters
    else:
        pool = all_masters

    as_int = _as_int(ref)
    if as_int is not None:
        for master in pool:
            if master.get("user_id") == as_int:
                return {"status": "ok", "master": master}
        return {"status": "not_found", "candidates": pool[:3]}

    query = str(ref)
    scored = sorted(
        (
            (catalog_mod.match_score(query, master.get("name") or ""), master)
            for master in pool
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    scored = [item for item in scored if item[0] >= 0.55]
    if not scored:
        return {"status": "not_found", "candidates": pool[:3]}

    candidates = [dict(master, score=round(score, 2)) for score, master in scored[:3]]
    top_score = scored[0][0]
    if len(scored) == 1:
        return {"status": "ok", "master": scored[0][1]}
    second_score = scored[1][0]
    if (
        top_score >= _CONFIDENT_SCORE
        and (top_score - second_score) >= _CONFIDENT_MARGIN
    ):
        return {"status": "ok", "master": scored[0][1]}
    return {"status": "ambiguous", "candidates": candidates}
