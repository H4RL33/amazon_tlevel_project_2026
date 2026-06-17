from pydantic import BaseModel


class TLevelResponse(BaseModel):
    id: int
    topic_id: int
    name: str
    entry_requirements: str
    how_to_apply: str

    model_config = {"from_attributes": True}


class TopicResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    accent_colour: str

    model_config = {"from_attributes": True}


class TopicDetailResponse(TopicResponse):
    t_levels: list[TLevelResponse]
    model_config = {"from_attributes": True}
