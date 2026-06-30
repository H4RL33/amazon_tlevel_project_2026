import json
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)

_VECTOR_DIM = 1024  # titan-embed-text-v2 output dimension


def embed_text(text: str) -> list[float] | None:
    """
    Generate a 1024-dim embedding vector using Amazon Titan Embed Text v2 via Bedrock.
    Returns None if Bedrock is unavailable or embedding is disabled; callers should skip
    the DB write in that case.
    """
    settings = get_settings()

    if settings.SKIP_EMBEDDINGS:
        return None

    model_id = settings.BEDROCK_EMBEDDING_MODEL_ID
    try:
        client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
        body = json.dumps({"inputText": text[:8000], "dimensions": _VECTOR_DIM, "normalize": True})
        response = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        result = json.loads(response["body"].read())
        return result["embedding"]
    except (BotoCoreError, ClientError, KeyError) as exc:
        logger.warning("Bedrock embedding failed, skipping: %s", exc)
        return None
