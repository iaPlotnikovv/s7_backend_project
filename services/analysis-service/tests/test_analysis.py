import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from app.ml_service import serialize_passenger
from app.ml_service import get_all_results
from httpx import AsyncClient


def _make_result() -> dict:
    return {
        "profile_id": str(uuid.uuid4()),
        "cluster": 0,
        "serialized_text": "Passenger: male, age 30. Flights: SVO to AER, economy class...",
        "x": 1.23,
        "y": 4.56,
    }


# ─── GET /health ──────────────────────────────────────────────────────────────

async def test_health(client: AsyncClient):
    response = await client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


# ─── GET /analysis/results ────────────────────────────────────────────────────

async def test_get_results_empty(client: AsyncClient):
    with patch(
        "app.routes.ml_service.get_all_results",
        new=AsyncMock(return_value=[]),
    ):
        response = await client.get("/analysis/results")

    assert response.status_code == 200
    assert response.json() == []


async def test_get_results_with_data(client: AsyncClient):
    fake_results = [_make_result(), _make_result()]
    with patch(
        "app.routes.ml_service.get_all_results",
        new=AsyncMock(return_value=fake_results),
    ):
        response = await client.get("/analysis/results")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert 'profile_id' in data[0]
    assert 'serialized_text' in data[0]
    


async def test_get_results_unauthorized(unauth_client: AsyncClient):
    response = await unauth_client.get("/analysis/results")
    assert response.status_code == 401
    
    
async def test_invalid_token(unauth_client: AsyncClient):
    response = await unauth_client.get(
        "/analysis/results",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


# ─── POST /analysis ───────────────────────────────────────────────────────────

async def test_post_analysis_smoke(client: AsyncClient):
    """Smoke test: пайплайн не падает, возвращает список."""
    fake_results = [_make_result()]
    with patch(
        "app.routes.ml_service.run_analysis",
        new=AsyncMock(return_value=fake_results),
    ):
        response = await client.post("/analysis")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_post_analysis_unauthorized(unauth_client: AsyncClient):
    response = await unauth_client.post("/analysis")
    assert response.status_code == 401
    
    
def test_serialize_passenger():
    passenger = {
        "gender": "male",
        "age": 30,
        "flights": [{
            "origin": "SVO",
            "destination": "AER",
            "departure_date": "2024-08-20",
            "booking_date": "2024-08-15",
            "seat_class": "economy",
            "revenue_usd": 150.0,
        }]
    }
    result = serialize_passenger(passenger)
    assert "Passenger: male, age 30" in result
    assert "SVO to AER" in result
    assert "economy class" in result
    assert "5 days in advance" in result  



async def test_get_all_results_empty():
    mock_session = MagicMock()                          # сессия — обычный Mock
    mock_result = MagicMock()                           # результат execute
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)  # только execute — async

    result = await get_all_results(mock_session)
    assert result== []