"""CRUD-тесты MeasureUnit против реального PostgreSQL.

Покрывают полный цикл Create/Read/Update/Delete через сервис, т.е. сквозь
цепочку Service -> UnitOfWork -> Repository.

Дополнительно проверяем, что данные реально персистятся в БД — читаем их
напрямую через engine (мимо UoW/identity map сервиса).
"""

from sqlalchemy import text

from src.services import MeasureUnitService
from src.context import current_user_id
from src.schemas.measure_unit import MeasureUnitCreate, MeasureUnitUpdate


async def test_create(measure_unit_service: MeasureUnitService):
    created = await measure_unit_service.create(MeasureUnitCreate(title="килограмм"))

    assert created.measure_unit_id is not None
    assert created.title == "килограмм"


async def test_get_by_pk(measure_unit_service):
    created = await measure_unit_service.create(MeasureUnitCreate(title="литр"))

    fetched = await measure_unit_service.get(created.measure_unit_id)

    assert fetched is not None
    assert fetched.measure_unit_id == created.measure_unit_id
    assert fetched.title == "литр"


async def test_get_multi(measure_unit_service):
    await measure_unit_service.create(MeasureUnitCreate(title="шт"))
    await measure_unit_service.create(MeasureUnitCreate(title="м"))

    items = await measure_unit_service.get_multi()

    titles = {item.title for item in items}
    assert {"шт", "м"} <= titles
    assert len(items) >= 2


async def test_update(measure_unit_service):
    created = await measure_unit_service.create(MeasureUnitCreate(title="грамм"))

    updated = await measure_unit_service.update(
        created.measure_unit_id,
        MeasureUnitUpdate(title="миллиграмм"),
    )

    assert updated.title == "миллиграмм"
    refetched = await measure_unit_service.get(created.measure_unit_id)
    assert refetched.title == "миллиграмм"


async def test_delete(measure_unit_service):
    created = await measure_unit_service.create(MeasureUnitCreate(title="удалить"))

    await measure_unit_service.delete(created.measure_unit_id)

    assert await measure_unit_service.get(created.measure_unit_id) is None


async def test_create_sets_audit_user(measure_unit_service):
    token = current_user_id.set(77)
    try:
        created = await measure_unit_service.create(MeasureUnitCreate(title="аудит"))
    finally:
        current_user_id.reset(token)

    assert created.who_create == 77
    assert created.who_update == 77


async def test_create_persists_row_in_db(measure_unit_service, engine):
    created = await measure_unit_service.create(MeasureUnitCreate(title="кг"))

    async with engine.connect() as conn:
        row = await conn.execute(
            text("SELECT title FROM measure_unit WHERE measure_unit_id = :id"),
            {"id": created.measure_unit_id},
        )
        assert row.scalar_one() == "кг"


async def test_update_persists_row_in_db(measure_unit_service, engine):
    created = await measure_unit_service.create(MeasureUnitCreate(title="грамм"))
    await measure_unit_service.update(
        created.measure_unit_id,
        MeasureUnitUpdate(title="миллиграмм"),
    )

    async with engine.connect() as conn:
        title = await conn.scalar(
            text("SELECT title FROM measure_unit WHERE measure_unit_id = :id"),
            {"id": created.measure_unit_id},
        )
        assert title == "миллиграмм"


async def test_delete_removes_row_from_db(measure_unit_service, engine):
    created = await measure_unit_service.create(MeasureUnitCreate(title="удалить"))
    await measure_unit_service.delete(created.measure_unit_id)

    async with engine.connect() as conn:
        cnt = await conn.scalar(
            text("SELECT count(*) FROM measure_unit WHERE measure_unit_id = :id"),
            {"id": created.measure_unit_id},
        )
        assert cnt == 0
