from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


async def test_sync_route_extracts_claims_from_bearer_token(
    db_session: AsyncSession, monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.routers.auth.decode_id_token",
        lambda token: {
            "sub": "sub-from-token",
            "email": "fromtoken@example.com",
            "given_name": "Header",
            "family_name": "Claims",
        },
    )

    async def override_get_db():
        yield db_session

    from app.database import get_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/auth/sync",
                json={"first_name": "Header", "last_name": "Claims"},
                headers={"Authorization": "Bearer fake-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["cognito_sub"] == "sub-from-token"
    assert response.json()["email"] == "fromtoken@example.com"
