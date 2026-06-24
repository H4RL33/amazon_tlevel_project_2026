import pytest

from app.dependencies.auth import get_current_user_optional


async def test_get_current_user_optional_returns_none_without_authorization_header() -> None:
    """Anonymous requests (no Authorization header) must not crash callers like the
    Album detail route, which uses this dependency to support both logged-in and
    anonymous access."""
    result = await get_current_user_optional(authorization=None)
    assert result is None


async def test_get_current_user_optional_raises_when_authorization_header_present() -> None:
    """Real JWT/Cognito validation is a deferred, separately-tracked gap — when a
    header IS present we still raise NotImplementedError rather than silently
    treating the request as anonymous."""
    with pytest.raises(NotImplementedError):
        await get_current_user_optional(authorization="Bearer some-token")
