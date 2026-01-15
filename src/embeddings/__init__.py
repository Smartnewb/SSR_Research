"""Embedding service module."""

from .service import get_embedding, get_embeddings_batch
from .cache import get_embedding_cached

__all__ = ["get_embedding", "get_embeddings_batch", "get_embedding_cached"]
