"""Embedding generation using LiteLLM."""

from __future__ import annotations

import litellm
import structlog

logger = structlog.get_logger()


async def embed_texts(
    texts: list[str],
    model: str = "text-embedding-3-small",
) -> list[list[float]]:
    """Generate embeddings for a list of texts via LiteLLM."""
    response = await litellm.aembedding(model=model, input=texts)
    embeddings = [item["embedding"] for item in response.data]
    logger.debug("embeddings_generated", count=len(texts), model=model)
    return embeddings


async def embed_text(
    text: str,
    model: str = "text-embedding-3-small",
) -> list[float]:
    """Generate embedding for a single text."""
    results = await embed_texts([text], model=model)
    return results[0]
