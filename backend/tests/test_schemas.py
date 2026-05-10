def test_schemas_importable():
    from app.schemas.user import UserResponse, UserSyncRequest, UserTopicsRequest
    from app.schemas.topic import TLevelResponse, TopicDetailResponse, TopicResponse
    from app.schemas.content import (
        ContentDetailResponse,
        ContentListResponse,
        ContentType,
        TagResponse,
    )
    from app.schemas.feed import ProgressResponse, ProgressUpdateRequest

    assert ContentType.article == "article"
    assert ContentType.video == "video"

    # Verify field presence via model_fields
    assert "cognito_sub" in UserResponse.model_fields
    assert "accent_colour" in TopicResponse.model_fields
    assert "progress_pct" in ProgressUpdateRequest.model_fields
