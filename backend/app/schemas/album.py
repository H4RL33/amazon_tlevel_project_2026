from pydantic import BaseModel

from app.models.content import ContentType

__all__ = [
    "AlbumListResponse",
    "SnippetSummaryResponse",
    "SideResponse",
    "AlbumDetailResponse",
]


class AlbumListResponse(BaseModel):
    id: int
    t_level_id: int
    topic_id: int
    title: str
    description: str
    icon: str

    model_config = {"from_attributes": True}


class SnippetSummaryResponse(BaseModel):
    id: int
    title: str
    content_type: ContentType

    model_config = {"from_attributes": True}


class SideResponse(BaseModel):
    id: int
    title: str
    position: int
    snippets: list[SnippetSummaryResponse]


class AlbumDetailResponse(AlbumListResponse):
    sides: list[SideResponse]
    enrolled: bool | None = None
    completed_count: int | None = None
    total_count: int | None = None
    progress_pct: int | None = None
