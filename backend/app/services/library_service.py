import json

from sqlalchemy import select
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.album import Album, AlbumEnrolment, Side, SideContent
from app.models.content import Content
from app.models.library import UserSnippetSave
from app.models.user import User
from app.schemas.album import AlbumListResponse
from app.schemas.content import ContentResponse
from app.schemas.library import (
    ContentSearchResult,
    LibraryResponse,
    MentorResponse,
    MentorSource,
)
from app.services.embedding_service import embed_text, get_bedrock_client

LIBRARY_SEARCH_BOOST = 1.4
MENTOR_CONTEXT_CHUNKS = 6
MENTOR_PERSONAL_LIMIT = 5
MENTOR_GLOBAL_LIMIT = 10


def _vec_to_str(vec: list[float]) -> str:
    return "[" + ",".join(str(v) for v in vec) + "]"


async def _get_user_boosted_ids(
    db: AsyncSession, user: User
) -> tuple[set[int], set[int]]:
    """Return (saved_ids, boosted_ids) where boosted_ids = saved_ids | enrolled_content_ids."""
    saved_ids: set[int] = set(
        (await db.execute(
            select(UserSnippetSave.content_id).where(UserSnippetSave.user_id == user.id)
        )).scalars().all()
    )
    enrolled_album_ids: set[int] = set(
        (await db.execute(
            select(AlbumEnrolment.album_id).where(AlbumEnrolment.user_id == user.id)
        )).scalars().all()
    )
    enrolled_content_ids: set[int] = set()
    if enrolled_album_ids:
        enrolled_content_ids = set(
            (await db.execute(
                select(SideContent.content_id)
                .join(Side, Side.id == SideContent.side_id)
                .where(Side.album_id.in_(enrolled_album_ids))
            )).scalars().all()
        )
    return saved_ids, saved_ids | enrolled_content_ids


async def get_library(db: AsyncSession, user: User) -> LibraryResponse:
    enrolled_stmt = (
        select(Album)
        .join(AlbumEnrolment, AlbumEnrolment.album_id == Album.id)
        .where(AlbumEnrolment.user_id == user.id)
        .options(selectinload(Album.t_level))
    )
    albums = (await db.execute(enrolled_stmt)).scalars().all()

    # AlbumListResponse requires topic_id, which is not on Album directly.
    # It lives at album.t_level.topic_id — we loaded t_level via selectinload above.
    enrolled_albums = [
        AlbumListResponse(
            id=a.id,
            t_level_id=a.t_level_id,
            topic_id=a.t_level.topic_id,
            title=a.title,
            description=a.description,
            icon=a.icon,
        )
        for a in albums
    ]

    saved_stmt = (
        select(Content)
        .join(UserSnippetSave, UserSnippetSave.content_id == Content.id)
        .where(UserSnippetSave.user_id == user.id)
    )
    snippets = (await db.execute(saved_stmt)).scalars().all()
    saved_snippets = [ContentResponse.model_validate(s) for s in snippets]

    return LibraryResponse(enrolled_albums=enrolled_albums, saved_snippets=saved_snippets)


def _apply_boost(
    rows: list,
    boosted_ids: set[int],
    saved_ids: set[int],
) -> list[ContentSearchResult]:
    results = []
    seen: set[int] = set()
    for row in rows:
        if row.id in seen:
            continue
        seen.add(row.id)
        similarity = 1.0 - float(row.distance)
        if row.id in boosted_ids:
            similarity *= LIBRARY_SEARCH_BOOST
        results.append(
            ContentSearchResult(
                content_id=row.id,
                title=row.title,
                content_type=row.content_type,
                album_title=row.album_title,
                similarity_score=round(similarity, 4),
                is_saved=row.id in saved_ids,
            )
        )
    results.sort(key=lambda r: r.similarity_score, reverse=True)
    return results[:10]


async def semantic_search(db: AsyncSession, query: str, user: User) -> list[ContentSearchResult]:
    saved_ids, boosted_ids = await _get_user_boosted_ids(db, user)
    query_vec_str = _vec_to_str(embed_text(query))

    rows = (
        await db.execute(
            sa_text(
                """
                SELECT
                    c.id,
                    c.title,
                    c.content_type,
                    a.title AS album_title,
                    (c.embedding <=> :vec::vector) AS distance
                FROM content c
                LEFT JOIN side_content sc ON sc.content_id = c.id
                LEFT JOIN sides s ON s.id = sc.side_id
                LEFT JOIN albums a ON a.id = s.album_id
                WHERE c.embedding IS NOT NULL
                ORDER BY distance
                LIMIT 20
                """
            ),
            {"vec": query_vec_str},
        )
    ).fetchall()

    return _apply_boost(rows, boosted_ids=boosted_ids, saved_ids=saved_ids)


async def _fetch_mentor_context(db: AsyncSession, query_vec: list[float], user: User) -> list[dict]:
    vec_str = _vec_to_str(query_vec)
    _, personal_ids = await _get_user_boosted_ids(db, user)

    personal_rows = []
    if personal_ids:
        personal_rows = (
            await db.execute(
                sa_text(
                    """
                    SELECT id, title, body,
                           (embedding <=> :vec::vector) AS distance
                    FROM content
                    WHERE id = ANY(:ids) AND embedding IS NOT NULL
                    ORDER BY distance
                    LIMIT :lim
                    """
                ),
                {"vec": vec_str, "ids": list(personal_ids), "lim": MENTOR_PERSONAL_LIMIT},
            )
        ).fetchall()

    global_rows = (
        await db.execute(
            sa_text(
                """
                SELECT id, title, body,
                       (embedding <=> :vec::vector) AS distance
                FROM content
                WHERE embedding IS NOT NULL
                ORDER BY distance
                LIMIT :lim
                """
            ),
            {"vec": vec_str, "lim": MENTOR_GLOBAL_LIMIT},
        )
    ).fetchall()

    merged: dict[int, dict] = {}
    for row in global_rows:
        merged[row.id] = {
            "content_id": row.id,
            "title": row.title,
            "body": row.body or "",
            "score": 1.0 - float(row.distance),
        }
    for row in personal_rows:
        score = (1.0 - float(row.distance)) * LIBRARY_SEARCH_BOOST
        if row.id not in merged or score > merged[row.id]["score"]:
            merged[row.id] = {
                "content_id": row.id,
                "title": row.title,
                "body": row.body or "",
                "score": score,
            }

    ranked = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
    return ranked[:MENTOR_CONTEXT_CHUNKS]


async def mentor_query(db: AsyncSession, message: str, user: User) -> MentorResponse:
    settings = get_settings()
    query_vec = embed_text(message)
    chunks = await _fetch_mentor_context(db, query_vec, user)

    context_text = "\n\n".join(f"{c['title']}: {c['body'][:500]}" for c in chunks)

    prompt = (
        "You are the Dynamic Mentor for Living Campus, an Amazon T-Level education platform.\n"
        "Answer the student's question using the provided context from their learning materials.\n"
        "If the context doesn't cover the question, say so and answer from general knowledge.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Student question: {message}\n\nMentor:"
    )

    response = get_bedrock_client().invoke_model(
        modelId=settings.BEDROCK_GENERATION_MODEL_ID,
        body=json.dumps(
            {
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {"maxTokens": 512, "temperature": 0.7, "topP": 0.9},
            }
        ),
    )
    body = json.loads(response["body"].read())
    reply_text = body["output"]["message"]["content"][0]["text"].strip()

    sources = [MentorSource(content_id=c["content_id"], title=c["title"]) for c in chunks]
    return MentorResponse(reply=reply_text, sources=sources)
