from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.topic import TopicResponse
from app.schemas.user import UserResponse, UserTopicsRequest


async def get_me(db: AsyncSession, current_user: User) -> UserResponse:
    """
    Return the UserResponse for the authenticated user.
    Map the ORM User object to UserResponse (model_config from_attributes handles this).
    """
    raise NotImplementedError


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
    raise NotImplementedError


async def get_topics(
    db: AsyncSession, current_user: User
) -> list[TopicResponse]:
    """
    Return all Topics the current user has expressed interest in.
    Join UserTopicInterest → Topic, filter by current_user.id.
    """
    raise NotImplementedError
