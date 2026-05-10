def test_schemas_importable():
    from app.schemas.content import (
        ContentType,
    )
    from app.schemas.feed import ProgressUpdateRequest
    from app.schemas.topic import TopicResponse
    from app.schemas.user import UserResponse

    assert ContentType.article == "article"
    assert ContentType.video == "video"

    # Verify field presence via model_fields
    assert "cognito_sub" in UserResponse.model_fields
    assert "accent_colour" in TopicResponse.model_fields
    assert "progress_pct" in ProgressUpdateRequest.model_fields
