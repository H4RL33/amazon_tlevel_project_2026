import os

# Set env vars before any app module is imported, because get_settings() is
# called at module-level in database.py and cached via lru_cache.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings  # noqa: E402
from app.database import get_db  # noqa: E402
from app.dependencies.auth import get_current_user, get_current_user_optional  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.models.user import User  # noqa: E402


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(get_settings().DATABASE_URL)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_factory() as session:
                yield session
        finally:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
    finally:
        await engine.dispose()


@pytest.fixture
async def current_user(db_session: AsyncSession) -> User:
    user = User(
        cognito_sub="test-sub",
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def client(db_session: AsyncSession, current_user: User) -> AsyncClient:
    """
    Anonymous-by-default test client: get_db is overridden with the test session,
    get_current_user (required-auth routes) returns the fixture user, and
    get_current_user_optional returns None — i.e. requests look anonymous to any
    route using optional auth, unless you use `authenticated_client` instead.
    """

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return current_user

    async def override_get_current_user_optional():
        return None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_optional] = override_get_current_user_optional

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(client: AsyncClient, current_user: User) -> AsyncClient:
    """Same as `client`, but get_current_user_optional also returns the fixture user."""

    async def override_get_current_user_optional():
        return current_user

    app.dependency_overrides[get_current_user_optional] = override_get_current_user_optional
    yield client
