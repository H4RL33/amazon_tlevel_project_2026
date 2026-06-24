from httpx import AsyncClient

from app.models.user import User


async def test_create_avatar_upload_url_returns_upload_url_and_key(
    authenticated_client: AsyncClient, monkeypatch
) -> None:
    import app.services.user_service as user_service_module

    monkeypatch.setattr(
        user_service_module,
        "_generate_presigned_put_url",
        lambda key, content_type: "https://example-bucket.s3.amazonaws.com/signed-put",
    )

    response = await authenticated_client.post(
        "/users/me/avatar-upload-url", json={"content_type": "image/png"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["key"].endswith(".png")
    assert body["upload_url"] == "https://example-bucket.s3.amazonaws.com/signed-put"


async def test_update_avatar_persists_key(
    authenticated_client: AsyncClient, current_user: User, monkeypatch
) -> None:
    import app.services.user_service as user_service_module

    monkeypatch.setattr(
        user_service_module,
        "_generate_presigned_get_url",
        lambda key: f"https://example-bucket.s3.amazonaws.com/{key}?signed=1",
    )

    key = f"avatars/{current_user.id}/photo.jpg"
    response = await authenticated_client.patch("/users/me/avatar", json={"avatar_s3_key": key})

    assert response.status_code == 200
    assert response.json()["id"] is not None


async def test_update_avatar_rejects_a_key_outside_the_users_own_prefix(
    authenticated_client: AsyncClient, current_user: User
) -> None:
    response = await authenticated_client.patch(
        "/users/me/avatar",
        json={"avatar_s3_key": f"avatars/{current_user.id + 1}/photo.jpg"},
    )

    assert response.status_code == 403
