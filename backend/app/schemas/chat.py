from datetime import datetime

from pydantic import BaseModel


class ChatSessionSummary(BaseModel):
    id: int
    title: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageSource(BaseModel):
    content_id: int
    title: str


class ChatMessageRecord(BaseModel):
    id: int
    role: str
    text: str
    sources: list[ChatMessageSource] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionDetail(BaseModel):
    id: int
    title: str
    messages: list[ChatMessageRecord]


class ChatMessageRequest(BaseModel):
    message: str
