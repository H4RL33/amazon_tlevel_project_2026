import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentTag, ContentType, Tag
from app.models.topic import Topic
from app.services import content_service


async def _make_topic(db: AsyncSession) -> Topic:
    topic = Topic(
        slug="digital-infrastructure",
        name="Digital Infrastructure",
        description="...",
        accent_colour="#CC3300",
    )
    db.add(topic)
    await db.flush()
    return topic


async def test_get_content_returns_body_and_tags(db_session: AsyncSession) -> None:
    topic = await _make_topic(db_session)
    content = Content(
        title="What is Cloud Computing?",
        body="Cloud computing means renting computing power...",
        content_type=ContentType.article,
        topic_id=topic.id,
    )
    db_session.add(content)
    await db_session.flush()
    tag = Tag(name="cloud")
    db_session.add(tag)
    await db_session.flush()
    db_session.add(ContentTag(content_id=content.id, tag_id=tag.id))
    await db_session.commit()

    result = await content_service.get_content(db_session, content.id)

    assert result.id == content.id
    assert result.title == "What is Cloud Computing?"
    assert result.body == "Cloud computing means renting computing power..."
    assert result.media_url is None
    assert [t.name for t in result.tags] == ["cloud"]


async def test_get_content_generates_presigned_url_when_media_url_set(
    db_session: AsyncSession, monkeypatch
) -> None:
    topic = await _make_topic(db_session)
    content = Content(
        title="Intro Video",
        content_type=ContentType.video,
        topic_id=topic.id,
        media_url="videos/intro.mp4",
    )
    db_session.add(content)
    await db_session.commit()

    async def fake_get_presigned_url(key, expiry_seconds=900):
        return "https://signed-url"

    monkeypatch.setattr(content_service, "get_presigned_url", fake_get_presigned_url)

    result = await content_service.get_content(db_session, content.id)

    assert result.media_url == "https://signed-url"


async def test_get_content_raises_404_when_not_found(db_session: AsyncSession) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await content_service.get_content(db_session, 999)

    assert exc_info.value.status_code == 404


async def test_get_presigned_url_calls_boto3_generate_presigned_url(monkeypatch) -> None:
    captured = {}

    class FakeS3Client:
        def generate_presigned_url(self, operation, Params, ExpiresIn):
            captured["operation"] = operation
            captured["params"] = Params
            captured["expires_in"] = ExpiresIn
            return "https://example-bucket.s3.amazonaws.com/some-key?signed=1"

    monkeypatch.setattr(
        content_service.boto3, "client", lambda service, region_name: FakeS3Client()
    )

    url = await content_service.get_presigned_url("some-key", expiry_seconds=120)

    assert url == "https://example-bucket.s3.amazonaws.com/some-key?signed=1"
    assert captured["operation"] == "get_object"
    assert captured["params"]["Key"] == "some-key"
    assert captured["expires_in"] == 120
