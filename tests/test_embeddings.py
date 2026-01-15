"""Unit tests for embedding module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.embeddings.cache import (
    get_cache_key,
    get_embedding_cached,
    EmbeddingCache,
)


class TestCacheKey:
    """Tests for cache key generation."""

    def test_same_input_same_key(self):
        """Same text and model should produce same key."""
        key1 = get_cache_key("hello", "text-embedding-3-small")
        key2 = get_cache_key("hello", "text-embedding-3-small")
        assert key1 == key2

    def test_different_text_different_key(self):
        """Different text should produce different key."""
        key1 = get_cache_key("hello", "text-embedding-3-small")
        key2 = get_cache_key("world", "text-embedding-3-small")
        assert key1 != key2

    def test_different_model_different_key(self):
        """Different model should produce different key."""
        key1 = get_cache_key("hello", "text-embedding-3-small")
        key2 = get_cache_key("hello", "text-embedding-3-large")
        assert key1 != key2

    def test_key_is_hex_string(self):
        """Key should be a valid hex string."""
        key = get_cache_key("test", "model")
        assert all(c in "0123456789abcdef" for c in key)
        assert len(key) == 64  # SHA256 hex = 64 chars


class TestGetEmbeddingCached:
    """Tests for cached embedding retrieval."""

    @pytest.fixture
    def mock_embedding_fn(self):
        """Mock embedding function."""
        def embed(text: str, model: str) -> np.ndarray:
            np.random.seed(hash(text) % (2**32))
            return np.random.randn(1536).astype(np.float64)
        return embed

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_computes_embedding_on_miss(self, temp_cache_dir, mock_embedding_fn):
        """Should compute embedding when not in cache."""
        embedding = get_embedding_cached(
            "test text",
            model="test-model",
            cache_dir=temp_cache_dir,
            embedding_fn=mock_embedding_fn,
        )

        assert embedding.shape == (1536,)
        assert embedding.dtype == np.float64

    def test_returns_cached_on_hit(self, temp_cache_dir, mock_embedding_fn):
        """Should return cached embedding on subsequent calls."""
        embedding1 = get_embedding_cached(
            "test text",
            model="test-model",
            cache_dir=temp_cache_dir,
            embedding_fn=mock_embedding_fn,
        )

        call_count = 0
        def counting_fn(text: str, model: str) -> np.ndarray:
            nonlocal call_count
            call_count += 1
            return mock_embedding_fn(text, model)

        embedding2 = get_embedding_cached(
            "test text",
            model="test-model",
            cache_dir=temp_cache_dir,
            embedding_fn=counting_fn,
        )

        assert call_count == 0
        np.testing.assert_array_equal(embedding1, embedding2)

    def test_creates_cache_dir(self, mock_embedding_fn):
        """Should create cache directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "subdir" / "cache"

            get_embedding_cached(
                "test",
                cache_dir=cache_dir,
                embedding_fn=mock_embedding_fn,
            )

            assert cache_dir.exists()


class TestEmbeddingCache:
    """Tests for EmbeddingCache class."""

    @pytest.fixture
    def mock_embedding_fn(self):
        """Mock embedding function."""
        def embed(text: str, model: str) -> np.ndarray:
            np.random.seed(hash(text) % (2**32))
            return np.random.randn(1536).astype(np.float64)
        return embed

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def cache(self, temp_cache_dir, mock_embedding_fn):
        """Create cache instance."""
        return EmbeddingCache(
            cache_dir=temp_cache_dir,
            model="test-model",
            embedding_fn=mock_embedding_fn,
        )

    def test_get_computes_on_miss(self, cache):
        """Should compute embedding on cache miss."""
        embedding = cache.get("test text")

        assert embedding.shape == (1536,)
        assert cache.stats["miss_count"] == 1
        assert cache.stats["hit_count"] == 0

    def test_get_returns_cached_on_hit(self, cache):
        """Should return cached value and increment hit count."""
        cache.get("test text")
        cache.get("test text")

        assert cache.stats["miss_count"] == 1
        assert cache.stats["hit_count"] == 1

    def test_memory_cache(self, cache):
        """Should cache in memory."""
        cache.get("test text")

        assert cache.stats["memory_cache_size"] == 1
        assert len(cache._memory_cache) == 1

    def test_hit_rate(self, cache):
        """Should calculate correct hit rate."""
        cache.get("text1")
        cache.get("text1")
        cache.get("text2")
        cache.get("text2")
        cache.get("text2")

        assert cache.stats["hit_rate"] == pytest.approx(3 / 5)

    def test_preload(self, cache):
        """Should preload multiple texts."""
        texts = ["text1", "text2", "text3"]
        cache.preload(texts)

        assert cache.stats["memory_cache_size"] == 3
        assert cache.stats["miss_count"] == 3

    def test_clear_memory(self, cache):
        """Should clear memory cache."""
        cache.get("test text")
        cache.clear_memory()

        assert cache.stats["memory_cache_size"] == 0
        assert len(cache._memory_cache) == 0

    def test_clear_disk(self, cache, temp_cache_dir):
        """Should clear disk cache."""
        cache.get("test text")
        assert len(list(temp_cache_dir.glob("*.pkl"))) == 1

        cache.clear_disk()
        assert len(list(temp_cache_dir.glob("*.pkl"))) == 0

    def test_clear_all(self, cache, temp_cache_dir):
        """Should clear both memory and disk cache."""
        cache.get("test text")
        cache.clear_all()

        assert cache.stats["memory_cache_size"] == 0
        assert len(list(temp_cache_dir.glob("*.pkl"))) == 0

    def test_reset_stats(self, cache):
        """Should reset statistics."""
        cache.get("text1")
        cache.get("text1")
        cache.reset_stats()

        assert cache.stats["hit_count"] == 0
        assert cache.stats["miss_count"] == 0
        assert cache.stats["hit_rate"] == 0.0

    def test_disk_persistence(self, temp_cache_dir, mock_embedding_fn):
        """Should persist to disk and reload."""
        cache1 = EmbeddingCache(
            cache_dir=temp_cache_dir,
            embedding_fn=mock_embedding_fn,
        )
        embedding1 = cache1.get("test text")

        cache2 = EmbeddingCache(
            cache_dir=temp_cache_dir,
            embedding_fn=mock_embedding_fn,
        )
        cache2.clear_memory()

        embedding2 = cache2.get("test text")

        np.testing.assert_array_equal(embedding1, embedding2)
        assert cache2.stats["hit_count"] == 1
        assert cache2.stats["miss_count"] == 0
