from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.album import Album, AlbumEnrolment, Side, SideContent  # noqa: E402, F401
from app.models.content import Content, ContentTag, ContentType, Tag  # noqa: E402, F401
from app.models.progress import UserContentProgress  # noqa: E402, F401
from app.models.t_level import TLevel  # noqa: E402, F401
from app.models.topic import Topic  # noqa: E402, F401
from app.models.library import UserSnippetSave  # noqa: E402, F401
from app.models.user import User, UserTopicInterest  # noqa: E402, F401
