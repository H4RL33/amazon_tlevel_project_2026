from datetime import datetime

from app.models.user import User
from app.services.user_service import build_user_response


def test_build_user_response_has_no_avatar_url_when_avatar_s3_key_is_none() -> None:
    user = User(
        id=1,
        cognito_sub="sub-1",
        email="a@example.com",
        first_name="A",
        last_name="B",
        avatar_s3_key=None,
        created_at=datetime.now(),
    )
    response = build_user_response(user)
    assert response.avatar_url is None


def test_build_user_response_has_avatar_url_when_avatar_s3_key_is_set(monkeypatch) -> None:
    import app.services.user_service as user_service_module

    monkeypatch.setattr(
        user_service_module,
        "_generate_presigned_get_url",
        lambda key: f"https://example-bucket.s3.amazonaws.com/{key}?signed=1",
    )
    user = User(
        id=1,
        cognito_sub="sub-1",
        email="a@example.com",
        first_name="A",
        last_name="B",
        avatar_s3_key="avatars/1/photo.jpg",
        created_at=datetime.now(),
    )
    response = build_user_response(user)
    assert response.avatar_url == "https://example-bucket.s3.amazonaws.com/avatars/1/photo.jpg?signed=1"
