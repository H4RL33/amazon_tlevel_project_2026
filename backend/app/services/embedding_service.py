import json
from typing import Any

import boto3

from app.config import get_settings


EMBED_DIMENSIONS = 1024
_client: Any = None


def get_bedrock_client() -> Any:
    global _client
    if _client is None:
        settings = get_settings()
        _client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
    return _client


def embed_text(text: str) -> list[float]:
    settings = get_settings()
    if settings.SKIP_EMBEDDINGS:
        return [0.0] * EMBED_DIMENSIONS
    response = get_bedrock_client().invoke_model(
        modelId=settings.BEDROCK_EMBEDDING_MODEL_ID,
        body=json.dumps({"inputText": text[:8000], "dimensions": EMBED_DIMENSIONS, "normalize": True}),
    )
    return json.loads(response["body"].read())["embedding"]
