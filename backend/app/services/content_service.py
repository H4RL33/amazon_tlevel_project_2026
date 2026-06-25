import boto3
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.content import Content, ContentTag
from app.schemas.content import ContentDetailResponse, ContentListResponse, TagResponse


async def list_content(
    db: AsyncSession,
    topic_slug: str | None = None,
    t_level_id: int | None = None,
    content_type: str | None = None,
    tag: str | None = None,
) -> list[ContentListResponse]:
    """
    Return Content rows filtered by the provided query parameters.
    All filters are optional and combinable.
    Do not include body or media_url in list results.
    """
    raise NotImplementedError


async def get_content(db: AsyncSession, content_id: int) -> ContentDetailResponse:
    """
    Return a single Content item including body (Markdown) and a fresh
    pre-signed S3 URL in the media_url field (generated via get_presigned_url).
    Raise HTTP 404 if not found.
    """
    result = await db.execute(
        select(Content)
        .options(selectinload(Content.content_tags).selectinload(ContentTag.tag))
        .where(Content.id == content_id)
    )
    content = result.scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")

    media_url = await get_presigned_url(content.media_url) if content.media_url else None

    return ContentDetailResponse(
        id=content.id,
        title=content.title,
        content_type=content.content_type,
        topic_id=content.topic_id,
        t_level_id=content.t_level_id,
        tags=[TagResponse.model_validate(ct.tag) for ct in content.content_tags],
        created_at=content.created_at,
        body=content.body,
        media_url=media_url,
    )


async def get_s3_key(db: AsyncSession, content_id: int) -> str:
    """
    Return the raw S3 key stored in content.media_url for the given content_id.
    Raise HTTP 404 if not found. Raise HTTP 422 if media_url is null.
    Used by the audio-url endpoint to avoid fetching the full content row.
    """
    raise NotImplementedError


async def get_presigned_url(s3_key: str, expiry_seconds: int = 900) -> str:
    """
    Generate a pre-signed S3 URL for the given S3 key with the given TTL.
    """
    s3 = boto3.client("s3", region_name=get_settings().AWS_REGION)
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": get_settings().S3_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=expiry_seconds,
    )
