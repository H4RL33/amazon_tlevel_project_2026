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


async def test_topics_route_requires_auth(client):
    response = await client.get("/topics/")
    assert response.status_code == 401, (
        f"Expected 401, got {response.status_code} — route may not be registered"
    )


async def test_content_route_requires_auth(client):
    response = await client.get("/content/")
    assert response.status_code == 401


async def test_feed_route_requires_auth(client):
    response = await client.get("/feed")
    assert response.status_code == 401


async def test_progress_route_requires_auth(client):
    response = await client.get("/progress")
    assert response.status_code == 401


async def test_users_me_requires_auth(client):
    response = await client.get("/users/me")
    assert response.status_code == 401


async def test_auth_sync_endpoint_exists(client):
    # No auth required — but needs valid JSON body
    response = await client.post("/auth/sync", json={"first_name": "Test", "last_name": "User"})
    # 422 = route exists, body parsed, but service raises NotImplementedError → 500
    # 401 = route exists but requires auth (check router config)
    # 404 = route not registered (failure)
    assert response.status_code != 404, "POST /auth/sync not registered"
