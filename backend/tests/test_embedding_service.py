import json
from unittest.mock import MagicMock, patch

import pytest


def _make_bedrock_response(embedding: list[float]) -> dict:
    body_bytes = json.dumps({"embedding": embedding}).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_bytes
    return {"body": mock_body}


def test_embed_text_returns_1536_floats():
    fake_vec = [0.1] * 1536
    with patch("app.services.embedding_service.boto3.client") as mock_client:
        mock_client.return_value.invoke_model.return_value = _make_bedrock_response(fake_vec)
        from app.services.embedding_service import embed_text

        result = embed_text("hello world")
    assert len(result) == 1536
    assert result[0] == pytest.approx(0.1)


def test_embed_text_truncates_to_8000_chars():
    long_text = "x" * 10_000
    fake_vec = [0.0] * 1536
    with patch("app.services.embedding_service.boto3.client") as mock_client:
        mock_client.return_value.invoke_model.return_value = _make_bedrock_response(fake_vec)
        import importlib

        import app.services.embedding_service as mod

        importlib.reload(mod)
        mod.embed_text(long_text)
        call_args = mock_client.return_value.invoke_model.call_args
        body = json.loads(call_args.kwargs["body"])
        assert len(body["inputText"]) == 8000


def test_embed_text_returns_zeros_when_skip_embeddings(monkeypatch):
    monkeypatch.setenv("SKIP_EMBEDDINGS", "true")
    import importlib

    import app.config as cfg_mod
    import app.services.embedding_service as mod

    cfg_mod.get_settings.cache_clear()
    importlib.reload(mod)
    result = mod.embed_text("anything")
    assert result == [0.0] * 1536
    cfg_mod.get_settings.cache_clear()
