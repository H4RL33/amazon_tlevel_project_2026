from datetime import datetime

from pydantic import BaseModel


class UserSyncRequest(BaseModel):
    first_name: str
    last_name: str


class UserResponse(BaseModel):
    id: int
    cognito_sub: str
    email: str
    first_name: str
    last_name: str
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserTopicsRequest(BaseModel):
    topic_ids: list[int]


class AvatarUploadUrlRequest(BaseModel):
    content_type: str


class AvatarUploadUrlResponse(BaseModel):
    upload_url: str
    key: str


class AvatarUpdateRequest(BaseModel):
    avatar_s3_key: str
