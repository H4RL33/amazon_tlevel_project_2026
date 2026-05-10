from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.topic import TLevelResponse, TopicDetailResponse, TopicResponse
from app.services import topic_service

router = APIRouter(prefix="/topics", tags=["topics"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[TopicResponse], summary="List all topic areas")
async def list_topics(
    db: AsyncSession = Depends(get_db),
) -> list[TopicResponse]:
    return await topic_service.list_topics(db)


@router.get("/{slug}", response_model=TopicDetailResponse, summary="Get topic with T-levels")
async def get_topic(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> TopicDetailResponse:
    return await topic_service.get_topic_by_slug(db, slug)


@router.get(
    "/{slug}/t-levels/{t_level_id}",
    response_model=TLevelResponse,
    summary="Get T-level detail",
)
async def get_t_level(
    slug: str,
    t_level_id: int,
    db: AsyncSession = Depends(get_db),
) -> TLevelResponse:
    return await topic_service.get_t_level(db, slug, t_level_id)
