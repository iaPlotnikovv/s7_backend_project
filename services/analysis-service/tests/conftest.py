import os

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

from unittest.mock import MagicMock

import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.dependencies import get_db, get_current_user


async def _override_get_db():
    yield MagicMock()


async def _override_get_current_user():
    return "fake-user-id"


@pytest_asyncio.fixture
async def client():
    """Аутентифицированный клиент — get_current_user переопределён."""
    app.state.model = MagicMock()
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def unauth_client():
    """Неаутентифицированный клиент — get_current_user НЕ переопределён."""
    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()