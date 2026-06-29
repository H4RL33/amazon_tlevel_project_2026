import json

import boto3

from app.config import get_settings


def embed_text(text: str) -> list[float]:
    settings = get_settings()
    if settings.SKIP_EMBEDDINGS:
        return [0.0] * 1536
    client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
    response = client.invoke_model(
        modelId=settings.BEDROCK_EMBEDDING_MODEL_ID,
        body=json.dumps({"inputText": text[:8000]}),
    )
    return json.loads(response["body"].read())["embedding"]
