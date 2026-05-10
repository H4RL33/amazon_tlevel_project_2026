import enum
from datetime import datetime

from pydantic import BaseModel


class ContentType(str, enum.Enum):
    article = "article"
    audio = "audio"
    video = "video"


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
