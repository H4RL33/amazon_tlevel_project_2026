from unittest.mock import patch

from app.services import embedding_service


def test_get_bedrock_client_returns_singleton_and_constructs_once() -> None:
    embedding_service._client = None
    with patch("app.services.embedding_service.boto3.client") as mock_boto_client:
        mock_boto_client.return_value = object()

        first = embedding_service.get_bedrock_client()
        second = embedding_service.get_bedrock_client()

        assert first is second
        mock_boto_client.assert_called_once()

    embedding_service._client = None
