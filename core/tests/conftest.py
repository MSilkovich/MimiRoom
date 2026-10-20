"""Фикстуры для интеграционных тестов на реальном PostgreSQL.

Стратегия изоляции:
- На всю сессию тестов создаётся ОДНА уникальная схема в целевой БД.
- Все таблицы создаются внутри этой схемы (search_path).
- Имя схемы уникально (timestamp + uuid), поэтому её можно оставлять
  в БД для последующего разбора — удаление закомментировано.
- Между тестами данные не чистятся: каждый тест работает с уникальными
  данными; при необходимости можно добавить TRUNCATE-фикстуру.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import src.models  # noqa: F401
from src.models.base_model import Base
from src.repositories.uow import SqlAlchemyUnitOfWork
from src.services.measure_unit_service import MeasureUnitService


def _make_schema_name() -> str:
    """Уникальное имя схемы: test_YYYYMMDD_HHMMSS_<short_uuid>."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"test_{ts}_{uuid.uuid4().hex[:8]}"


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Engine, привязанный к уникальной тестовой схеме.

    `search_path` выставляется один раз на уровне соединения через
    connect-аргументы asyncpg, чтобы все последующие сессии попадали
    именно в нашу схему.
    """
    from config.database.db_config import settings_db

    schema = _make_schema_name()

    eng = create_async_engine(
        url=settings_db.database_url,
        echo=False,
        pool_pre_ping=True,
        poolclass=NullPool,
        # search_path применяется к каждому новому соединению из пула.
        connect_args={"server_settings": {"search_path": f"{schema},public"}},
    )

    # Создаём схему один раз на всю сессию.
    async with eng.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))

    print(f"\n[tests] using schema: {schema}")

    yield eng

    await eng.dispose()

    # cleanup_eng = create_async_engine(_get_test_db_url())
    # async with cleanup_eng.begin() as conn:
    #     await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    # await cleanup_eng.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _schema(engine):
    """Создаёт все таблицы внутри тестовой схемы один раз на сессию."""
    async with engine.begin() as conn:
        t = list(Base.metadata.tables.keys())

        await conn.run_sync(Base.metadata.create_all)

    yield

    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
def measure_unit_service(session_factory):
    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    return MeasureUnitService(uow_factory)
