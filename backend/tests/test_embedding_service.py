import json
from unittest.mock import MagicMock, patch

import pytest

import app.services.embedding_service as _embed_mod
from app.services.embedding_service import EMBED_DIMENSIONS


@pytest.fixture(autouse=True)
def reset_bedrock_singleton():
    """Reset the module-level client singleton before each test to prevent cross-test leakage."""
    _embed_mod._client = None
    yield
    _embed_mod._client = None


def _make_bedrock_response(embedding: list[float]) -> dict:
    body_bytes = json.dumps({"embedding": embedding}).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_bytes
    return {"body": mock_body}


def test_embed_text_returns_correct_dimension_floats():
    fake_vec = [0.1] * EMBED_DIMENSIONS
    with patch("app.services.embedding_service.boto3.client") as mock_client:
        mock_client.return_value.invoke_model.return_value = _make_bedrock_response(fake_vec)
        result = _embed_mod.embed_text("hello world")
    assert len(result) == EMBED_DIMENSIONS
    assert result[0] == pytest.approx(0.1)


def test_embed_text_truncates_to_8000_chars():
    long_text = "x" * 10_000
    fake_vec = [0.0] * EMBED_DIMENSIONS
    with patch("app.services.embedding_service.boto3.client") as mock_client:
        mock_client.return_value.invoke_model.return_value = _make_bedrock_response(fake_vec)
        _embed_mod.embed_text(long_text)
        call_args = mock_client.return_value.invoke_model.call_args
        body = json.loads(call_args.kwargs["body"])
        assert len(body["inputText"]) == 8000


def test_embed_text_returns_zeros_when_skip_embeddings(monkeypatch):
    monkeypatch.setenv("SKIP_EMBEDDINGS", "true")
    import importlib

    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()
    importlib.reload(_embed_mod)
    result = _embed_mod.embed_text("anything")
    assert result == [0.0] * EMBED_DIMENSIONS
    cfg_mod.get_settings.cache_clear()


def test_get_bedrock_client_returns_singleton():
    with patch("app.services.embedding_service.boto3.client") as mock_ctor:
        mock_ctor.return_value = MagicMock()
        c1 = _embed_mod.get_bedrock_client()
        c2 = _embed_mod.get_bedrock_client()
        assert c1 is c2
        assert mock_ctor.call_count == 1
