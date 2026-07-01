from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic import Topic
from app.models.user import User
from app.schemas.user import AvatarUploadUrlRequest, UserTopicsRequest
from app.services import user_service
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
    assert (
        response.avatar_url
        == "https://example-bucket.s3.amazonaws.com/avatars/1/photo.jpg?signed=1"
    )


async def _make_topic(db: AsyncSession, slug: str) -> Topic:
    topic = Topic(slug=slug, name=slug, description="...", accent_colour="#000000")
    db.add(topic)
    await db.flush()
    return topic


async def test_get_me_returns_user_response(db_session: AsyncSession) -> None:
    user = User(cognito_sub="sub-x", email="x@example.com", first_name="X", last_name="Y")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await user_service.get_me(db_session, user)
    assert response.cognito_sub == "sub-x"


async def test_set_topics_replaces_existing_interests(db_session: AsyncSession) -> None:
    user = User(cognito_sub="sub-y", email="y@example.com", first_name="X", last_name="Y")
    db_session.add(user)
    await db_session.flush()
    topic_a = await _make_topic(db_session, "topic-a")
    topic_b = await _make_topic(db_session, "topic-b")
    await db_session.commit()

    await user_service.set_topics(db_session, user, UserTopicsRequest(topic_ids=[topic_a.id]))
    result = await user_service.set_topics(
        db_session, user, UserTopicsRequest(topic_ids=[topic_b.id])
    )

    assert [t.id for t in result] == [topic_b.id]


async def test_set_topics_rejects_unknown_topic_id(db_session: AsyncSession) -> None:
    from fastapi import HTTPException

    user = User(cognito_sub="sub-z", email="z@example.com", first_name="X", last_name="Y")
    db_session.add(user)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await user_service.set_topics(db_session, user, UserTopicsRequest(topic_ids=[999]))
    assert exc_info.value.status_code == 422


async def test_get_topics_returns_only_this_users_interests(db_session: AsyncSession) -> None:
    user = User(cognito_sub="sub-w", email="w@example.com", first_name="X", last_name="Y")
    db_session.add(user)
    await db_session.flush()
    topic_a = await _make_topic(db_session, "topic-c")
    await db_session.commit()

    await user_service.set_topics(db_session, user, UserTopicsRequest(topic_ids=[topic_a.id]))
    result = await user_service.get_topics(db_session, user)

    assert [t.id for t in result] == [topic_a.id]


async def test_create_avatar_upload_url_rejects_unsupported_content_type() -> None:
    from fastapi import HTTPException

    user = User(id=1, cognito_sub="sub-1", email="a@example.com", first_name="A", last_name="B")
    with pytest.raises(HTTPException) as exc_info:
        user_service.create_avatar_upload_url(
            user, AvatarUploadUrlRequest(content_type="text/plain")
        )
    assert exc_info.value.status_code == 422


async def test_create_avatar_upload_url_returns_a_jpg_key_for_jpeg(monkeypatch) -> None:
    monkeypatch.setattr(
        user_service,
        "_generate_presigned_put_url",
        lambda key, content_type: f"https://example-bucket.s3.amazonaws.com/{key}?put=1",
    )
    user = User(id=42, cognito_sub="sub-1", email="a@example.com", first_name="A", last_name="B")

    result = user_service.create_avatar_upload_url(
        user, AvatarUploadUrlRequest(content_type="image/jpeg")
    )

    assert result.key.startswith("avatars/42/")
    assert result.key.endswith(".jpg")
    assert result.upload_url.endswith("?put=1")


async def test_set_avatar_persists_the_key_and_returns_user_response(
    db_session: AsyncSession, monkeypatch
) -> None:
    monkeypatch.setattr(
        user_service,
        "_generate_presigned_get_url",
        lambda key: f"https://example-bucket.s3.amazonaws.com/{key}?signed=1",
    )
    user = User(cognito_sub="sub-avatar", email="avatar@example.com", first_name="A", last_name="B")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    key = f"avatars/{user.id}/photo.jpg"
    response = await user_service.set_avatar(db_session, user, key)

    assert user.avatar_s3_key == key
    assert response.id == user.id


async def test_set_avatar_rejects_a_key_outside_the_users_own_prefix(
    db_session: AsyncSession,
) -> None:
    from fastapi import HTTPException

    user = User(
        cognito_sub="sub-avatar-2", email="avatar2@example.com", first_name="A", last_name="B"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    with pytest.raises(HTTPException) as exc_info:
        await user_service.set_avatar(db_session, user, f"avatars/{user.id + 1}/photo.jpg")
    assert exc_info.value.status_code == 403


async def test_update_username_allows_single_spaces_between_words(
    db_session: AsyncSession,
) -> None:
    user = User(cognito_sub="sub-space-1", email="space1@example.com", first_name="A", last_name="B")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    result = await user_service.update_username(db_session, user, "harley welsh")

    assert result.username == "harley welsh"


async def test_update_username_strips_leading_and_trailing_space(
    db_session: AsyncSession,
) -> None:
    user = User(cognito_sub="sub-space-2", email="space2@example.com", first_name="A", last_name="B")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    result = await user_service.update_username(db_session, user, "  harley  ")

    assert result.username == "harley"


async def test_update_username_rejects_double_spaces() -> None:
    from fastapi import HTTPException

    user = User(cognito_sub="sub-space-3", email="space3@example.com", first_name="A", last_name="B")

    with pytest.raises(HTTPException) as exc_info:
        await user_service.update_username(None, user, "harley  welsh")  # type: ignore[arg-type]
    assert exc_info.value.status_code == 422


async def test_update_username_still_rejects_special_characters() -> None:
    from fastapi import HTTPException

    user = User(cognito_sub="sub-space-4", email="space4@example.com", first_name="A", last_name="B")

    with pytest.raises(HTTPException) as exc_info:
        await user_service.update_username(None, user, "harley@welsh")  # type: ignore[arg-type]
    assert exc_info.value.status_code == 422
