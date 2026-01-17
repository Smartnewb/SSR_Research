"""SSR Calculator - Core algorithm for semantic similarity rating."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

import numpy as np
from numpy.typing import NDArray

from .anchors import POSITIVE_ANCHOR, NEGATIVE_ANCHOR
from .utils import cosine_similarity

logger = logging.getLogger(__name__)


class OutlierType(Enum):
    """Classification of projection outlier types."""

    NORMAL = "normal"
    EXTREME_NEGATIVE = "extreme_negative"  # < 0: More negative than anchor
    EXTREME_POSITIVE = "extreme_positive"  # > 1: More positive than anchor


@dataclass
class SSRResult:
    """Extended SSR calculation result with outlier detection."""

    score: float
    raw_projection: float
    outlier_type: OutlierType
    is_outlier: bool

    @property
    def outlier_magnitude(self) -> float:
        """How far outside [0, 1] the raw projection is."""
        if self.raw_projection < 0:
            return abs(self.raw_projection)
        elif self.raw_projection > 1:
            return self.raw_projection - 1
        return 0.0


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
        Calculate SSR using the paper's formula.

        Based on: "Can LLMs Simulate Surveys?" (arxiv:2510.08338)

        Formula: score = (sim_pos - sim_neg + 2) / 4

        This normalizes (sim_pos - sim_neg) / 2 from [-1, 1] to [0, 1]:
        - sim_pos: cosine similarity to positive anchor
        - sim_neg: cosine similarity to negative anchor
        - Raw score = (sim_pos - sim_neg) / 2 ∈ [-1, 1]
        - Normalized = (raw + 1) / 2 ∈ [0, 1]

        Args:
            response_vec: Embedding of the response text

        Returns:
            SSR score in [0, 1]
        """
        self._ensure_initialized()

        sim_pos = cosine_similarity(response_vec, self.pos_vec)
        sim_neg = cosine_similarity(response_vec, self.neg_vec)

        # Paper formula: (sim_pos - sim_neg) / 2, then normalize to [0, 1]
        raw_score = (sim_pos - sim_neg) / 2  # Range: [-1, 1]
        score = (raw_score + 1) / 2  # Normalize to [0, 1]

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
        result = self.calculate_projection_with_outlier_detection(response_vec)
        return result.score

    def calculate_projection_with_outlier_detection(
        self, response_vec: NDArray[np.float64]
    ) -> SSRResult:
        """
        Calculate SSR using projection method with outlier detection.

        Detects when responses fall outside the anchor range:
        - EXTREME_NEGATIVE: Projection < 0 (more negative than negative anchor)
        - EXTREME_POSITIVE: Projection > 1 (more positive than positive anchor)

        These outliers may indicate:
        - Anchor calibration issues
        - Persona exhibiting extreme reactions
        - Potential model hallucination

        Args:
            response_vec: Embedding of the response text

        Returns:
            SSRResult with score, raw projection, and outlier classification
        """
        self._ensure_initialized()

        axis = self.pos_vec - self.neg_vec
        axis_norm_sq = np.dot(axis, axis)

        if axis_norm_sq == 0:
            return SSRResult(
                score=0.5,
                raw_projection=0.5,
                outlier_type=OutlierType.NORMAL,
                is_outlier=False,
            )

        raw_projection = float(
            np.dot(response_vec - self.neg_vec, axis) / axis_norm_sq
        )

        outlier_type = OutlierType.NORMAL
        is_outlier = False

        if raw_projection < 0:
            outlier_type = OutlierType.EXTREME_NEGATIVE
            is_outlier = True
            logger.warning(
                f"EXTREME_OUTLIER: Projection {raw_projection:.3f} < 0. "
                "Response is more negative than the negative anchor. "
                "Consider reviewing anchor calibration or persona behavior."
            )
        elif raw_projection > 1:
            outlier_type = OutlierType.EXTREME_POSITIVE
            is_outlier = True
            logger.warning(
                f"EXTREME_OUTLIER: Projection {raw_projection:.3f} > 1. "
                "Response is more positive than the positive anchor. "
                "Consider reviewing anchor calibration or persona behavior."
            )

        score = float(np.clip(raw_projection, 0.0, 1.0))

        return SSRResult(
            score=score,
            raw_projection=raw_projection,
            outlier_type=outlier_type,
            is_outlier=is_outlier,
        )

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
            # Vectorized paper formula: (sim_pos - sim_neg + 2) / 4
            norms_resp = np.linalg.norm(response_vecs, axis=1)
            norm_pos = np.linalg.norm(self.pos_vec)
            norm_neg = np.linalg.norm(self.neg_vec)

            dots_pos = np.dot(response_vecs, self.pos_vec)
            dots_neg = np.dot(response_vecs, self.neg_vec)

            sims_pos = dots_pos / (norms_resp * norm_pos + 1e-10)
            sims_neg = dots_neg / (norms_resp * norm_neg + 1e-10)

            # Paper formula: (sim_pos - sim_neg) / 2, then normalize to [0, 1]
            raw_scores = (sims_pos - sims_neg) / 2  # Range: [-1, 1]
            scores = (raw_scores + 1) / 2  # Normalize to [0, 1]

            return scores

        elif method == "projection":
            result = self.calculate_batch_with_outlier_detection(response_vecs)
            return result["scores"]

        else:
            raise ValueError(f"Unknown method: {method}. Use 'simple' or 'projection'.")

    def calculate_batch_with_outlier_detection(
        self,
        response_vecs: NDArray[np.float64],
    ) -> dict:
        """
        Calculate SSR for multiple responses with outlier detection.

        Args:
            response_vecs: Array of shape (N, embedding_dim)

        Returns:
            Dict containing:
            - scores: Array of SSR scores, shape (N,)
            - raw_projections: Array of raw projections before clipping
            - outlier_mask: Boolean array indicating outliers
            - outlier_types: Array of OutlierType enums
            - outlier_stats: Summary statistics of outliers
        """
        self._ensure_initialized()

        axis = self.pos_vec - self.neg_vec
        axis_norm_sq = np.dot(axis, axis)

        if axis_norm_sq == 0:
            n = len(response_vecs)
            return {
                "scores": np.full(n, 0.5),
                "raw_projections": np.full(n, 0.5),
                "outlier_mask": np.zeros(n, dtype=bool),
                "outlier_types": [OutlierType.NORMAL] * n,
                "outlier_stats": {"total": 0, "extreme_negative": 0, "extreme_positive": 0},
            }

        centered = response_vecs - self.neg_vec
        raw_projections = np.dot(centered, axis) / axis_norm_sq
        scores = np.clip(raw_projections, 0.0, 1.0)

        extreme_neg_mask = raw_projections < 0
        extreme_pos_mask = raw_projections > 1
        outlier_mask = extreme_neg_mask | extreme_pos_mask

        outlier_types = []
        for i in range(len(raw_projections)):
            if extreme_neg_mask[i]:
                outlier_types.append(OutlierType.EXTREME_NEGATIVE)
            elif extreme_pos_mask[i]:
                outlier_types.append(OutlierType.EXTREME_POSITIVE)
            else:
                outlier_types.append(OutlierType.NORMAL)

        outlier_stats = {
            "total": int(outlier_mask.sum()),
            "extreme_negative": int(extreme_neg_mask.sum()),
            "extreme_positive": int(extreme_pos_mask.sum()),
            "outlier_rate": float(outlier_mask.sum() / len(raw_projections)),
        }

        if outlier_stats["total"] > 0:
            logger.warning(
                f"BATCH_OUTLIER_SUMMARY: {outlier_stats['total']} outliers detected "
                f"({outlier_stats['outlier_rate']:.1%}). "
                f"Extreme negative: {outlier_stats['extreme_negative']}, "
                f"Extreme positive: {outlier_stats['extreme_positive']}. "
                "Consider reviewing anchor calibration."
            )

        return {
            "scores": scores,
            "raw_projections": raw_projections,
            "outlier_mask": outlier_mask,
            "outlier_types": outlier_types,
            "outlier_stats": outlier_stats,
        }

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
