from datetime import datetime

from pydantic import BaseModel

from app.models.content import ContentType

__all__ = ["ContentType", "TagResponse", "ContentResponse", "ContentListResponse", "ContentDetailResponse"]


class ContentResponse(BaseModel):
    id: int
    title: str
    content_type: ContentType
    media_url: str | None = None
    topic_id: int
    t_level_id: int | None = None

    model_config = {"from_attributes": True}


class TagResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ContentListResponse(BaseModel):
    id: int
    title: str
    content_type: ContentType
    topic_id: int
    t_level_id: int | None
    tags: list[TagResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentDetailResponse(ContentListResponse):
    body: str | None
    media_url: str | None  # Pre-signed S3 URL generated at request time; not stored in DB
    is_saved: bool = False
