from pydantic import BaseModel


class UserStatsResponse(BaseModel):
    total_xp: int
    level: int
    snippets_completed: int
    albums_completed: int
