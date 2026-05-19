from unittest.mock import patch, AsyncMock
import uuid

from httpx import AsyncClient



# ─── GET /health ────────────────────────────────────────────────────────────

async def test_health(client: AsyncClient):
    response = await client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


# ─── GET /passengers/flights ─────────────────────────────────────────────────

def _make_passenger(profile_id: uuid.UUID | None = None) -> dict:
    """Фабрика: создаёт один валидный объект пассажира."""
    return {
        "profile_id": str(profile_id or uuid.uuid4()),
        "gender": "male",
        "age": 30,
        "flights": [
            {
                "origin": "SVO",
                "destination": "AER",
                "departure_date": "2024-08-15",
                "booking_date": "2024-06-20",
                "seat_class": "economy",
                "revenue_usd": 150.0,
            }
        ],
    }


async def test_get_flights_returns_list(client: AsyncClient):
    """Happy path: сервис возвращает пассажиров → endpoint сериализует список."""
    fake_passengers = [_make_passenger() for _ in range(2) ]  # создай список из 2 пассажиров через _make_passenger

    with patch(
        'app.routes.service.get_all_passengers',  
        new=AsyncMock(return_value=fake_passengers)         
    ):
        response = await client.get("/passengers/flights")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert "profile_id" in data[0]
    assert "flights" in data[0]


async def test_get_flights_empty(client: AsyncClient):
    """Edge case: БД пуста → endpoint возвращает [] со статусом 200."""
    with patch(
        'app.routes.service.get_all_passengers',
        new=AsyncMock(return_value=[]),
    ):
        response = await client.get("/passengers/flights")

    assert response.status_code == 200
    assert response.json() == []