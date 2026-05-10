from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.content import ContentListResponse


class ProgressResponse(BaseModel):
    content_id: int
    last_viewed_at: datetime
    progress_pct: int
    content: ContentListResponse

    model_config = {"from_attributes": True}


class ProgressUpdateRequest(BaseModel):
    progress_pct: int = Field(ge=0, le=100)
