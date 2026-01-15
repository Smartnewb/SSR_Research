"""Embedding service for text vectorization."""

import os
from typing import Optional

import numpy as np
from numpy.typing import NDArray


def get_embedding(
    text: str,
    model: str = "text-embedding-3-small",
    client: Optional["openai.OpenAI"] = None,
) -> NDArray[np.float64]:
    """
    Get embedding vector for a single text.

    Args:
        text: Input text to embed
        model: OpenAI embedding model
        client: Optional OpenAI client (creates one if not provided)

    Returns:
        NumPy array of shape (1536,) for text-embedding-3-small
    """
    if client is None:
        import openai
        client = openai.OpenAI()

    response = client.embeddings.create(
        input=text,
        model=model,
    )

    embedding = np.array(response.data[0].embedding, dtype=np.float64)
    return embedding


def get_embeddings_batch(
    texts: list[str],
    model: str = "text-embedding-3-small",
    batch_size: int = 100,
    client: Optional["openai.OpenAI"] = None,
) -> NDArray[np.float64]:
    """
    Get embeddings for multiple texts (batched for efficiency).

    OpenAI allows up to 2048 inputs per request, but we use batch_size=100
    for safety and memory management.

    Args:
        texts: List of texts to embed
        model: Embedding model
        batch_size: Max texts per API call (default: 100)
        client: Optional OpenAI client

    Returns:
        NumPy array of shape (N, embedding_dim) where N = len(texts)
    """
    if client is None:
        import openai
        client = openai.OpenAI()

    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        response = client.embeddings.create(
            input=batch,
            model=model,
        )

        batch_embeddings = [
            item.embedding
            for item in sorted(response.data, key=lambda x: x.index)
        ]
        all_embeddings.extend(batch_embeddings)

    return np.array(all_embeddings, dtype=np.float64)


class EmbeddingService:
    """
    Embedding service with caching and cost tracking.

    Provides a higher-level interface for embedding operations.
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        client: Optional["openai.OpenAI"] = None,
    ):
        """
        Initialize embedding service.

        Args:
            model: Embedding model to use
            client: Optional OpenAI client
        """
        self.model = model
        self._client = client
        self._token_count = 0
        self._request_count = 0

    @property
    def client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            import openai
            self._client = openai.OpenAI()
        return self._client

    def embed(self, text: str) -> NDArray[np.float64]:
        """Embed a single text."""
        embedding = get_embedding(text, model=self.model, client=self.client)
        self._request_count += 1
        return embedding

    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> NDArray[np.float64]:
        """Embed multiple texts."""
        embeddings = get_embeddings_batch(
            texts,
            model=self.model,
            batch_size=batch_size,
            client=self.client,
        )
        self._request_count += (len(texts) + batch_size - 1) // batch_size
        return embeddings

    @property
    def stats(self) -> dict:
        """Get usage statistics."""
        return {
            "model": self.model,
            "request_count": self._request_count,
        }

    def reset_stats(self) -> None:
        """Reset usage statistics."""
        self._token_count = 0
        self._request_count = 0
