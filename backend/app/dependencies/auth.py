from app.models.user import User


async def get_current_user() -> User:
    # Replace this with a real implementation (local JWT or Cognito) when auth is decided.
    raise NotImplementedError


async def get_current_user_optional() -> User | None:
    # Replace this with a real implementation (local JWT or Cognito) when auth is decided.
    # Must return None when no Authorization header is present, rather than raising —
    # used by routes that behave differently for logged-in vs anonymous requests
    # without requiring auth to succeed.
    raise NotImplementedError
