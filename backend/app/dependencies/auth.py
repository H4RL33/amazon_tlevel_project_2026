from app.models.user import User


async def get_current_user() -> User:
    # Replace this with a real implementation (local JWT or Cognito) when auth is decided.
    raise NotImplementedError
