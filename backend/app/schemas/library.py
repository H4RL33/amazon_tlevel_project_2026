from pydantic import BaseModel

from app.models.content import ContentType
from app.schemas.album import AlbumListResponse
from app.schemas.content import ContentResponse


class LibraryResponse(BaseModel):
    enrolled_albums: list[AlbumListResponse]
    saved_snippets: list[ContentResponse]


class ContentSearchResult(BaseModel):
    content_id: int
    title: str
    content_type: ContentType
    album_title: str | None
    similarity_score: float
    is_saved: bool


class MentorRequest(BaseModel):
    message: str


class MentorSource(BaseModel):
    content_id: int
    title: str


class MentorResponse(BaseModel):
    reply: str
    sources: list[MentorSource]
