from httpx import AsyncClient


# ─── POST /auth/register ──────────────────────────────────────────────────────

async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "strongpass123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True
    assert "hashed_password" not in data


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "strongpass123"}
    await client.post("/auth/register", json=payload)
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 400


# ─── POST /auth/login ─────────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "strongpass123"},
    )
    response = await client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "strongpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "wp@example.com", "password": "strongpass123"},
    )
    response = await client.post(
        "/auth/login",
        data={"username": "wp@example.com", "password": "WRONGPASSWORD"},
    )
    assert response.status_code == 401


# ─── GET /auth/me ─────────────────────────────────────────────────────────────

async def test_get_me_success(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "me@example.com", "password": "strongpass123"},
    )
    login_resp = await client.post(
        "/auth/login",
        data={"username": "me@example.com", "password": "strongpass123"},
    )
    token = login_resp.json()["access_token"]

    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


async def test_get_me_unauthorized(client: AsyncClient):
    response = await client.get("/auth/me")
    assert response.status_code == 401
    
async def test_invalid_token(client: AsyncClient):
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token"},
    )
    assert response.status_code == 401
 
