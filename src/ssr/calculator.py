"""SSR Calculator - Core algorithm for semantic similarity rating."""

from typing import Callable, Optional

import numpy as np
from numpy.typing import NDArray

from .anchors import POSITIVE_ANCHOR, NEGATIVE_ANCHOR
from .utils import cosine_similarity


class SSRCalculator:
    """
    Semantic Similarity Rating calculator.

    Converts free-text responses into numerical purchase intent scores
    using embedding similarity to semantic anchors.
    """

    def __init__(
        self,
        pos_anchor: str = POSITIVE_ANCHOR,
        neg_anchor: str = NEGATIVE_ANCHOR,
        embedding_fn: Optional[Callable[[str], NDArray[np.float64]]] = None,
    ):
        """
        Initialize calculator with anchor texts.

        Args:
            pos_anchor: Positive anchor text
            neg_anchor: Negative anchor text
            embedding_fn: Function that takes text and returns np.array
        """
        self.pos_anchor_text = pos_anchor
        self.neg_anchor_text = neg_anchor
        self.embedding_fn = embedding_fn

        self.pos_vec: Optional[NDArray[np.float64]] = None
        self.neg_vec: Optional[NDArray[np.float64]] = None
        self._initialized = False

    def initialize_anchors(self) -> None:
        """Compute and cache anchor embeddings."""
        if self.embedding_fn is None:
            raise ValueError("Embedding function not set")

        self.pos_vec = self.embedding_fn(self.pos_anchor_text)
        self.neg_vec = self.embedding_fn(self.neg_anchor_text)
        self._initialized = True

    def set_anchor_embeddings(
        self,
        pos_vec: NDArray[np.float64],
        neg_vec: NDArray[np.float64],
    ) -> None:
        """
        Set pre-computed anchor embeddings directly.

        Args:
            pos_vec: Positive anchor embedding
            neg_vec: Negative anchor embedding
        """
        self.pos_vec = pos_vec
        self.neg_vec = neg_vec
        self._initialized = True

    def _ensure_initialized(self) -> None:
        """Ensure anchors are initialized before calculation."""
        if not self._initialized or self.pos_vec is None:
            raise ValueError(
                "Anchors not initialized. "
                "Call initialize_anchors() or set_anchor_embeddings() first."
            )

    def calculate_simple(self, response_vec: NDArray[np.float64]) -> float:
        """
        Calculate SSR using simplified method.

        The score is derived from similarity to the positive anchor,
        normalized to [0, 1] range.

        Formula: score = (sim_pos + 1) / 2
        Where sim_pos is cosine similarity to positive anchor.

        Args:
            response_vec: Embedding of the response text

        Returns:
            SSR score in [0, 1]
        """
        self._ensure_initialized()

        sim_pos = cosine_similarity(response_vec, self.pos_vec)
        score = (sim_pos + 1) / 2

        return score

    def calculate_projection(self, response_vec: NDArray[np.float64]) -> float:
        """
        Calculate SSR using full projection method.

        Projects the response vector onto the semantic axis,
        then normalizes based on anchor positions.

        Formula:
        axis = pos_vec - neg_vec
        projection = (response_vec - neg_vec) · axis / ||axis||²
        score = clamp(projection, 0, 1)

        Args:
            response_vec: Embedding of the response text

        Returns:
            SSR score in [0, 1]
        """
        self._ensure_initialized()

        axis = self.pos_vec - self.neg_vec
        axis_norm_sq = np.dot(axis, axis)

        if axis_norm_sq == 0:
            return 0.5

        projection = np.dot(response_vec - self.neg_vec, axis) / axis_norm_sq
        score = float(np.clip(projection, 0.0, 1.0))

        return score

    def calculate_batch(
        self,
        response_vecs: NDArray[np.float64],
        method: str = "simple",
    ) -> NDArray[np.float64]:
        """
        Calculate SSR for multiple responses (vectorized).

        Args:
            response_vecs: Array of shape (N, embedding_dim)
            method: "simple" or "projection"

        Returns:
            Array of SSR scores, shape (N,)
        """
        self._ensure_initialized()

        if method == "simple":
            dots = np.dot(response_vecs, self.pos_vec)
            norms_resp = np.linalg.norm(response_vecs, axis=1)
            norm_pos = np.linalg.norm(self.pos_vec)

            sims = dots / (norms_resp * norm_pos + 1e-10)
            scores = (sims + 1) / 2

            return scores

        elif method == "projection":
            axis = self.pos_vec - self.neg_vec
            axis_norm_sq = np.dot(axis, axis)

            if axis_norm_sq == 0:
                return np.full(len(response_vecs), 0.5)

            centered = response_vecs - self.neg_vec
            projections = np.dot(centered, axis) / axis_norm_sq
            scores = np.clip(projections, 0.0, 1.0)

            return scores

        else:
            raise ValueError(f"Unknown method: {method}. Use 'simple' or 'projection'.")

    def calculate(
        self,
        response_vec: NDArray[np.float64],
        method: str = "simple",
    ) -> float:
        """
        Calculate SSR score using specified method.

        Args:
            response_vec: Embedding of the response text
            method: "simple" or "projection"

        Returns:
            SSR score in [0, 1]
        """
        if method == "simple":
            return self.calculate_simple(response_vec)
        elif method == "projection":
            return self.calculate_projection(response_vec)
        else:
            raise ValueError(f"Unknown method: {method}. Use 'simple' or 'projection'.")
