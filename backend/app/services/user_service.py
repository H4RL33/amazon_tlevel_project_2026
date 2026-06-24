import boto3
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.topic import Topic
from app.models.user import User, UserTopicInterest
from app.schemas.topic import TopicResponse
from app.schemas.user import UserResponse, UserTopicsRequest


def _generate_presigned_get_url(s3_key: str, expiry_seconds: int = 3600) -> str:
    s3 = boto3.client("s3", region_name=get_settings().AWS_REGION)
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": get_settings().S3_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=expiry_seconds,
    )


def build_user_response(user: User) -> UserResponse:
    avatar_url = _generate_presigned_get_url(user.avatar_s3_key) if user.avatar_s3_key else None
    return UserResponse(
        id=user.id,
        cognito_sub=user.cognito_sub,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        avatar_url=avatar_url,
        created_at=user.created_at,
    )


async def get_me(db: AsyncSession, current_user: User) -> UserResponse:
    """
    Return the UserResponse for the authenticated user.
    Map the ORM User object to UserResponse (model_config from_attributes handles this).
    """
    return build_user_response(current_user)


async def set_topics(
    db: AsyncSession, current_user: User, payload: UserTopicsRequest
) -> list[TopicResponse]:
    """
    Replace all UserTopicInterest rows for current_user with the given topic_ids.

    - Delete all existing UserTopicInterest rows for this user.
    - Insert new rows for each id in payload.topic_ids.
    - Raise HTTP 422 if any topic_id does not exist in the topics table.
    - Return the updated list of TopicResponse objects.
    """
    if payload.topic_ids:
        result = await db.execute(select(Topic.id).where(Topic.id.in_(payload.topic_ids)))
        found_ids = {row[0] for row in result.all()}
        missing = set(payload.topic_ids) - found_ids
        if missing:
            raise HTTPException(status_code=422, detail=f"Unknown topic_ids: {sorted(missing)}")

    await db.execute(
        delete(UserTopicInterest).where(UserTopicInterest.user_id == current_user.id)
    )
    for topic_id in payload.topic_ids:
        db.add(UserTopicInterest(user_id=current_user.id, topic_id=topic_id))
    await db.commit()

    return await get_topics(db, current_user)


async def get_topics(db: AsyncSession, current_user: User) -> list[TopicResponse]:
    """
    Return all Topics the current user has expressed interest in.
    Join UserTopicInterest → Topic, filter by current_user.id.
    """
    result = await db.execute(
        select(Topic)
        .join(UserTopicInterest, UserTopicInterest.topic_id == Topic.id)
        .where(UserTopicInterest.user_id == current_user.id)
    )
    return [TopicResponse.model_validate(topic) for topic in result.scalars().all()]
