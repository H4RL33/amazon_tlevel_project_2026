from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.content import Content, ContentTag
from app.models.library import UserSnippetSave
from app.models.user import User
from app.schemas.content import ContentDetailResponse, TagResponse


async def save_snippet(db: AsyncSession, content_id: int, user: User) -> None:
    existing = await db.get(UserSnippetSave, (user.id, content_id))
    if existing is not None:
        return
    db.add(UserSnippetSave(user_id=user.id, content_id=content_id))
    await db.commit()


async def unsave_snippet(db: AsyncSession, content_id: int, user: User) -> None:
    await db.execute(
        delete(UserSnippetSave).where(
            UserSnippetSave.user_id == user.id,
            UserSnippetSave.content_id == content_id,
        )
    )
    await db.commit()


async def get_snippet(
    db: AsyncSession,
    content_id: int,
    user: User | None,
) -> ContentDetailResponse:
    snippet = (
        await db.execute(
            select(Content)
            .where(Content.id == content_id)
            .options(selectinload(Content.content_tags).selectinload(ContentTag.tag))
        )
    ).scalar_one_or_none()
    if snippet is None:
        raise HTTPException(status_code=404, detail="Snippet not found")

    is_saved = False
    if user is not None:
        save_row = await db.get(UserSnippetSave, (user.id, content_id))
        is_saved = save_row is not None

    tags = [TagResponse(id=ct.tag.id, name=ct.tag.name) for ct in snippet.content_tags]

    return ContentDetailResponse(
        id=snippet.id,
        title=snippet.title,
        content_type=snippet.content_type,
        body=snippet.body,
        media_url=snippet.media_url,
        topic_id=snippet.topic_id,
        t_level_id=snippet.t_level_id,
        tags=tags,
        created_at=snippet.created_at,
        is_saved=is_saved,
    )
