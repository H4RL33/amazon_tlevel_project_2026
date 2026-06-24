from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.album import AlbumDetailResponse, AlbumListResponse
from app.services import album_service

router = APIRouter(prefix="/albums", tags=["albums"])


@router.get("/", response_model=list[AlbumListResponse], summary="List albums")
async def list_albums(
    t_level_id: int | None = None,
    topic: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[AlbumListResponse]:
    return await album_service.list_albums(db, t_level_id, topic)


@router.get(
    "/{album_id}",
    response_model=AlbumDetailResponse,
    response_model_exclude_none=True,
    summary="Get album detail with sides and snippets",
)
async def get_album(
    album_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> AlbumDetailResponse:
    return await album_service.get_album_detail(db, album_id, current_user)


@router.post("/{album_id}/enrol", status_code=204, summary="Enrol in an album")
async def enrol(
    album_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await album_service.enrol(db, album_id, current_user)


@router.delete("/{album_id}/enrol", status_code=204, summary="Un-enrol from an album")
async def unenrol(
    album_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await album_service.unenrol(db, album_id, current_user)
