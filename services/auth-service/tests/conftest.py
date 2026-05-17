import os

# Env-переменные выставляем ДО импорта app-модулей.
# pydantic-settings читает os.environ при Settings() — это происходит при импорте config.py.
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base
from app.dependencies import get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def client():
    """
    Поднимает приложение с SQLite in-memory вместо PostgreSQL.

    ASGITransport отправляет только scope["type"] = "http".
    Lifespan-события (startup/shutdown) он не генерирует,
    поэтому create_all из main.py никогда не запускается —
    ни боевой, ни переопределённый.

    Таблицы создаём вручную до старта клиента.
    get_db переопределяем чтобы запросы шли в тестовую SQLite, не PostgreSQL.

    StaticPool — обязателен для sqlite:///:memory:.
    Без него каждое соединение получает отдельную БД,
    таблицы из create_all не видны сессии в get_db.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
    )

    # Создаём схему вручную — lifespan не запускается через ASGITransport
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
