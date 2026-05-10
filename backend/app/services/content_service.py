from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.content import ContentDetailResponse, ContentListResponse


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
    raise NotImplementedError


async def get_presigned_url(s3_key: str, expiry_seconds: int = 900) -> str:
    """
    Generate a pre-signed S3 URL for the given S3 key with the given TTL.

    Use boto3:
        import boto3
        s3 = boto3.client("s3", region_name=get_settings().AWS_REGION)
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": get_settings().S3_BUCKET_NAME, "Key": s3_key},
            ExpiresIn=expiry_seconds,
        )
    """
    raise NotImplementedError
