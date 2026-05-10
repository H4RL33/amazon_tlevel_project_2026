def test_models_importable():
    from app.models.content import Content, ContentType
    from app.models.progress import UserContentProgress
    from app.models.t_level import TLevel
    from app.models.topic import Topic
    from app.models.user import User

    assert User.__tablename__ == "users"
    assert Topic.__tablename__ == "topics"
    assert TLevel.__tablename__ == "t_levels"
    assert Content.__tablename__ == "content"
    assert UserContentProgress.__tablename__ == "user_content_progress"
    assert ContentType.article == "article"
    assert ContentType.audio == "audio"
    assert ContentType.video == "video"
