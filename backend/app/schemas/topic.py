from pydantic import BaseModel

from app.schemas.album import AlbumListResponse


class TLevelResponse(BaseModel):
    id: int
    topic_id: int
    name: str
    entry_requirements: str
    how_to_apply: str

    model_config = {"from_attributes": True}


class TLevelWithAlbumsResponse(TLevelResponse):
    albums: list[AlbumListResponse]


class TopicResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    accent_colour: str

    model_config = {"from_attributes": True}


class TopicDetailResponse(TopicResponse):
    t_levels: list[TLevelWithAlbumsResponse]
