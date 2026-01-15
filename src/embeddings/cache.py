"""File-based caching for embeddings."""

import hashlib
import pickle
from pathlib import Path
from typing import Callable, Optional

import numpy as np
from numpy.typing import NDArray


CACHE_DIR = Path(".cache/embeddings")


def get_cache_key(text: str, model: str) -> str:
    """Generate cache key from text and model."""
    content = f"{text}|{model}"
    return hashlib.sha256(content.encode()).hexdigest()


def get_embedding_cached(
    text: str,
    model: str = "text-embedding-3-small",
    cache_dir: Optional[Path] = None,
    embedding_fn: Optional[Callable[[str, str], NDArray[np.float64]]] = None,
) -> NDArray[np.float64]:
    """
    Get embedding with file-based caching.

    Cache key is hash of (text, model). Embeddings are stored as pickle files.

    Args:
        text: Text to embed
        model: Embedding model name
        cache_dir: Directory for cache files (default: .cache/embeddings)
        embedding_fn: Function to compute embedding if not cached

    Returns:
        NumPy array embedding vector
    """
    if cache_dir is None:
        cache_dir = CACHE_DIR

    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_key = get_cache_key(text, model)
    cache_file = cache_dir / f"{cache_key}.pkl"

    if cache_file.exists():
        with open(cache_file, "rb") as f:
            return pickle.load(f)

    if embedding_fn is None:
        from .service import get_embedding
        embedding_fn = get_embedding

    embedding = embedding_fn(text, model)

    with open(cache_file, "wb") as f:
        pickle.dump(embedding, f)

    return embedding


class EmbeddingCache:
    """
    Embedding cache with in-memory and file-based storage.

    Provides a higher-level interface for cached embeddings.
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        model: str = "text-embedding-3-small",
        embedding_fn: Optional[Callable[[str, str], NDArray[np.float64]]] = None,
    ):
        """
        Initialize embedding cache.

        Args:
            cache_dir: Directory for cache files
            model: Default embedding model
            embedding_fn: Function to compute embeddings
        """
        self.cache_dir = cache_dir or CACHE_DIR
        self.model = model
        self._embedding_fn = embedding_fn
        self._memory_cache: dict[str, NDArray[np.float64]] = {}
        self._hit_count = 0
        self._miss_count = 0

    @property
    def embedding_fn(self):
        """Lazy-load embedding function."""
        if self._embedding_fn is None:
            from .service import get_embedding
            self._embedding_fn = get_embedding
        return self._embedding_fn

    def get(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> NDArray[np.float64]:
        """
        Get embedding with caching.

        First checks memory cache, then file cache, then computes.

        Args:
            text: Text to embed
            model: Embedding model (uses default if not specified)

        Returns:
            Embedding vector
        """
        model = model or self.model
        cache_key = get_cache_key(text, model)

        if cache_key in self._memory_cache:
            self._hit_count += 1
            return self._memory_cache[cache_key]

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if cache_file.exists():
            self._hit_count += 1
            with open(cache_file, "rb") as f:
                embedding = pickle.load(f)
            self._memory_cache[cache_key] = embedding
            return embedding

        self._miss_count += 1
        embedding = self.embedding_fn(text, model)

        self._memory_cache[cache_key] = embedding
        with open(cache_file, "wb") as f:
            pickle.dump(embedding, f)

        return embedding

    def preload(self, texts: list[str], model: Optional[str] = None) -> None:
        """Preload embeddings into memory cache."""
        for text in texts:
            self.get(text, model)

    def clear_memory(self) -> None:
        """Clear in-memory cache."""
        self._memory_cache.clear()

    def clear_disk(self) -> None:
        """Clear disk cache."""
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()

    def clear_all(self) -> None:
        """Clear both memory and disk cache."""
        self.clear_memory()
        self.clear_disk()

    @property
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "memory_cache_size": len(self._memory_cache),
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": (
                self._hit_count / (self._hit_count + self._miss_count)
                if (self._hit_count + self._miss_count) > 0
                else 0.0
            ),
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._hit_count = 0
        self._miss_count = 0
