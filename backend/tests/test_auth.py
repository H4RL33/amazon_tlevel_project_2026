import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_health_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_missing_token_returns_401(client):
    response = await client.get("/users/me")
    assert response.status_code == 401


async def test_invalid_token_returns_401(client):
    response = await client.get("/users/me", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401
