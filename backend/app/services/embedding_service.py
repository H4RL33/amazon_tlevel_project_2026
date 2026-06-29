import json

import boto3

from app.config import get_settings


EMBED_DIMENSIONS = 1024


def embed_text(text: str) -> list[float]:
    settings = get_settings()
    if settings.SKIP_EMBEDDINGS:
        return [0.0] * EMBED_DIMENSIONS
    client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
    response = client.invoke_model(
        modelId=settings.BEDROCK_EMBEDDING_MODEL_ID,
        body=json.dumps({"inputText": text[:8000], "dimensions": EMBED_DIMENSIONS, "normalize": True}),
    )
    return json.loads(response["body"].read())["embedding"]
