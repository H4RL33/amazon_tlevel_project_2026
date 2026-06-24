from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserSyncRequest
from app.services import auth_service


async def test_sync_user_creates_a_new_user_when_none_exists(db_session: AsyncSession) -> None:
    response = await auth_service.sync_user(
        db_session,
        cognito_sub="sub-new",
        email="new@example.com",
        payload=UserSyncRequest(first_name="New", last_name="User"),
    )

    assert response.cognito_sub == "sub-new"
    assert response.first_name == "New"

    result = await db_session.execute(select(User).where(User.cognito_sub == "sub-new"))
    assert result.scalar_one() is not None


async def test_sync_user_updates_name_on_repeat_login(db_session: AsyncSession) -> None:
    await auth_service.sync_user(
        db_session,
        cognito_sub="sub-existing",
        email="existing@example.com",
        payload=UserSyncRequest(first_name="Old", last_name="Name"),
    )

    response = await auth_service.sync_user(
        db_session,
        cognito_sub="sub-existing",
        email="existing@example.com",
        payload=UserSyncRequest(first_name="New", last_name="Name2"),
    )

    assert response.first_name == "New"
    assert response.last_name == "Name2"

    result = await db_session.execute(select(User).where(User.cognito_sub == "sub-existing"))
    rows = result.scalars().all()
    assert len(rows) == 1
