from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.content import ContentDetailResponse, ContentListResponse
from app.services import content_service

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/", response_model=list[ContentListResponse], summary="List content")
async def list_content(
    topic: str | None = None,
    t_level_id: int | None = None,
    content_type: str | None = None,
    tag: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[ContentListResponse]:
    return await content_service.list_content(db, topic, t_level_id, content_type, tag)


@router.get(
    "/{content_id}",
    response_model=ContentDetailResponse,
    summary="Get content item with body and media URL",
)
async def get_content(
    content_id: int,
    db: AsyncSession = Depends(get_db),
) -> ContentDetailResponse:
    return await content_service.get_content(db, content_id)


@router.get(
    "/{content_id}/audio-url",
    response_model=dict[str, str],
    summary="Get fresh pre-signed S3 URL for audio",
)
async def get_audio_url(
    content_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    s3_key = await content_service.get_s3_key(db, content_id)
    url = await content_service.get_presigned_url(s3_key)
    return {"url": url}
