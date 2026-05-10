from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.content import ContentListResponse
from app.schemas.feed import ProgressResponse, ProgressUpdateRequest


async def get_feed(db: AsyncSession, current_user: User) -> list[ContentListResponse]:
    """
    Return a personalised list of Content items for the current user.

    Algorithm (implement in this order):
    1. Find all topic_ids from the user's UserTopicInterest rows.
    2. Find all content_ids the user has already started (UserContentProgress).
    3. Return Content rows whose topic_id is in the user's topics,
       ordered by created_at DESC.

    Future enhancement (do not implement now): re-rank by tag overlap with
    the user's engagement history.
    """
    raise NotImplementedError


async def get_progress(db: AsyncSession, current_user: User) -> list[ProgressResponse]:
    """
    Return the user's in-progress Content items (progress_pct < 100),
    ordered by last_viewed_at DESC.
    Join UserContentProgress → Content to populate the nested content field.
    """
    raise NotImplementedError


async def upsert_progress(
    db: AsyncSession,
    current_user: User,
    content_id: int,
    payload: ProgressUpdateRequest,
) -> None:
    """
    Insert or update a UserContentProgress row.

    - If a row exists for (user_id, content_id): update progress_pct and last_viewed_at.
    - If no row exists: insert a new row.
    - Raise HTTP 404 if content_id does not exist in the content table.
    """
    raise NotImplementedError
