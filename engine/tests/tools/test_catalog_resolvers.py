"""Тесты каталога и резолвера (без сети)."""

import pytest

from src.tools import catalog as catalog_mod
from src.tools import resolvers

SERVICES = [
    {
        "service_id": 3,
        "title": "Стрижка кошки",
        "price": "1500.00",
        "duration_minutes": 60,
        "breed_title": "средняя",
        "masters": [{"user_id": 1, "name": "Анна", "surname": "Иванова"}],
    },
    {
        "service_id": 4,
        "title": "Стрижка собаки",
        "price": "2000.00",
        "duration_minutes": 90,
        "breed_title": "крупная",
        "masters": [{"user_id": 2, "name": "Ирина"}],
    },
    {
        "service_id": 5,
        "title": "Комплексный груминг",
        "price": "2500.00",
        "duration_minutes": 120,
        "breed_title": None,
        "masters": [],
    },
]

MASTERS = [
    {
        "user_id": 1,
        "name": "Анна",
        "surname": "Иванова",
        "services": [{"service_id": 3, "title": "Стрижка кошки"}],
    },
    {
        "user_id": 2,
        "name": "Ирина",
        "services": [{"service_id": 4, "title": "Стрижка собаки"}],
    },
]


@pytest.fixture
def catalog():
    return catalog_mod.build_catalog(SERVICES, MASTERS)


def test_build_catalog_projects_compact_cards(catalog):
    card = catalog["services"][0]
    assert card["service_id"] == 3
    assert card["title"] == "Стрижка кошки"
    assert card["masters"][0]["name"] == "Анна Иванова"
    assert catalog["masters"][0]["name"] == "Анна Иванова"


def test_find_services_handles_typos(catalog):
    matches = catalog_mod.find_services("стрыжка", catalog)
    titles = {m["title"] for m in matches}
    assert "Стрижка кошки" in titles
    assert "Стрижка собаки" in titles


def test_find_default_service(catalog):
    fallback = catalog_mod.find_default_service(catalog)
    assert fallback is not None
    assert fallback["service_id"] == 5


def test_render_block_contains_ids_and_masters(catalog):
    text = catalog_mod.render_catalog_block(catalog)
    assert "id=3" in text
    assert "МАСТЕРА" in text
    assert "Стрижка кошки" in text


def test_resolve_service_by_id_and_name(catalog):
    assert resolvers.resolve_service(3, catalog)["status"] == "ok"
    resolved = resolvers.resolve_service("комплексный", catalog)
    assert resolved["status"] == "ok"
    assert resolved["service"]["service_id"] == 5


def test_resolve_service_ambiguous_on_two_similar(catalog):
    resolved = resolvers.resolve_service("стрыжка", catalog)
    assert resolved["status"] == "ambiguous"
    assert len(resolved["candidates"]) >= 2


def test_resolve_service_not_found(catalog):
    assert resolvers.resolve_service("маникюр", catalog)["status"] == "not_found"


def test_resolve_master(catalog):
    assert resolvers.resolve_master("Анна", catalog)["status"] == "ok"
    assert resolvers.resolve_master(2, catalog)["status"] == "ok"


@pytest.mark.asyncio
async def test_find_service_handler_fallback(monkeypatch, catalog):
    from src.tools.handlers import handlers

    async def fake_catalog(*args, **kwargs):
        return catalog

    monkeypatch.setattr(handlers, "_get_catalog", fake_catalog)

    result = await handlers.find_service(user_id=0, query="мойка лабрадора")
    assert result["matches"] == []
    assert result["fallback"]["service_id"] == 5
