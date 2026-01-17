"""Semantic anchor text definitions for SSR calculation."""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

POSITIVE_ANCHOR = "I would definitely buy this product."
NEGATIVE_ANCHOR = "I would never buy this product."

SIMILARITY_WARNING_THRESHOLD = 0.6
SIMILARITY_CRITICAL_THRESHOLD = 0.8

SUGGESTED_ALTERNATIVES = {
    "high_contrast": {
        "positive": "I absolutely love this and must have it immediately.",
        "negative": "I completely hate this and would never consider it.",
    },
    "extreme_polar": {
        "positive": "This is perfect. Take my money right now.",
        "negative": "This is worthless garbage. Absolutely not.",
    },
}


@dataclass
class AnchorValidationResult:
    """Result of anchor orthogonality validation."""

    is_valid: bool
    similarity: float
    warning_level: str  # "ok", "warning", "critical"
    message: str
    suggested_alternative: Optional[dict] = None

ALTERNATIVE_ANCHORS = {
    "default": {
        "positive": "I would definitely buy this product.",
        "negative": "I would never buy this product.",
    },
    "extreme": {
        "positive": "This is the best product I've ever seen. I'm buying it immediately.",
        "negative": "This is completely useless. I would never waste money on this.",
    },
    "neutral": {
        "positive": "I would purchase this product.",
        "negative": "I would not purchase this product.",
    },
    "b2b": {
        "positive": "This tool would significantly improve our workflow. We should adopt it.",
        "negative": "This tool doesn't fit our needs. We won't be using it.",
    },
}


def get_anchors(anchor_type: str = "default") -> tuple[str, str]:
    """
    Get anchor texts by type.

    Args:
        anchor_type: One of 'default', 'extreme', 'neutral', 'b2b'

    Returns:
        Tuple of (positive_anchor, negative_anchor)
    """
    if anchor_type not in ALTERNATIVE_ANCHORS:
        raise ValueError(f"Unknown anchor type: {anchor_type}")

    anchors = ALTERNATIVE_ANCHORS[anchor_type]
    return anchors["positive"], anchors["negative"]


def _cosine_similarity(vec_a: NDArray[np.float64], vec_b: NDArray[np.float64]) -> float:
    """Compute cosine similarity between two vectors."""
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


def validate_anchor_orthogonality(
    pos_embedding: NDArray[np.float64],
    neg_embedding: NDArray[np.float64],
    warning_threshold: float = SIMILARITY_WARNING_THRESHOLD,
    critical_threshold: float = SIMILARITY_CRITICAL_THRESHOLD,
) -> AnchorValidationResult:
    """
    Validate that positive and negative anchors are sufficiently orthogonal.

    In text-embedding-3-small space, anchors that are too similar
    (similarity > 0.6) will reduce score discriminability.

    Args:
        pos_embedding: Embedding vector for positive anchor
        neg_embedding: Embedding vector for negative anchor
        warning_threshold: Similarity above this triggers warning (default: 0.6)
        critical_threshold: Similarity above this triggers critical (default: 0.8)

    Returns:
        AnchorValidationResult with validation details
    """
    similarity = _cosine_similarity(pos_embedding, neg_embedding)

    if similarity >= critical_threshold:
        result = AnchorValidationResult(
            is_valid=False,
            similarity=similarity,
            warning_level="critical",
            message=(
                f"CRITICAL: Anchor similarity {similarity:.3f} >= {critical_threshold}. "
                "Score discriminability severely compromised. "
                "Please use more contrasting anchor texts."
            ),
            suggested_alternative=SUGGESTED_ALTERNATIVES["extreme_polar"],
        )
        logger.error(result.message)
        return result

    if similarity >= warning_threshold:
        result = AnchorValidationResult(
            is_valid=True,
            similarity=similarity,
            warning_level="warning",
            message=(
                f"WARNING: Anchor similarity {similarity:.3f} >= {warning_threshold}. "
                "Score discriminability may be reduced. "
                "Consider using more contrasting anchor texts."
            ),
            suggested_alternative=SUGGESTED_ALTERNATIVES["high_contrast"],
        )
        logger.warning(result.message)
        return result

    return AnchorValidationResult(
        is_valid=True,
        similarity=similarity,
        warning_level="ok",
        message=f"Anchors are sufficiently orthogonal (similarity: {similarity:.3f})",
    )


class AnchorHealthCheck:
    """Health check utility for anchor embeddings."""

    def __init__(
        self,
        embedding_fn: callable,
        warning_threshold: float = SIMILARITY_WARNING_THRESHOLD,
        critical_threshold: float = SIMILARITY_CRITICAL_THRESHOLD,
    ):
        """
        Initialize anchor health checker.

        Args:
            embedding_fn: Function that takes text and returns embedding vector
            warning_threshold: Similarity threshold for warning
            critical_threshold: Similarity threshold for critical error
        """
        self.embedding_fn = embedding_fn
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

    def check(
        self,
        pos_text: str = POSITIVE_ANCHOR,
        neg_text: str = NEGATIVE_ANCHOR,
    ) -> AnchorValidationResult:
        """
        Check anchor orthogonality by computing embeddings.

        Args:
            pos_text: Positive anchor text
            neg_text: Negative anchor text

        Returns:
            AnchorValidationResult with validation details
        """
        pos_embedding = self.embedding_fn(pos_text)
        neg_embedding = self.embedding_fn(neg_text)

        return validate_anchor_orthogonality(
            pos_embedding,
            neg_embedding,
            self.warning_threshold,
            self.critical_threshold,
        )

    def check_all_types(self) -> dict[str, AnchorValidationResult]:
        """
        Check orthogonality for all predefined anchor types.

        Returns:
            Dict mapping anchor type to validation result
        """
        results = {}
        for anchor_type in ALTERNATIVE_ANCHORS:
            pos_text, neg_text = get_anchors(anchor_type)
            results[anchor_type] = self.check(pos_text, neg_text)
        return results

    def find_best_anchors(self) -> tuple[str, AnchorValidationResult]:
        """
        Find the anchor type with best orthogonality.

        Returns:
            Tuple of (best_anchor_type, validation_result)
        """
        results = self.check_all_types()
        best_type = min(results, key=lambda k: results[k].similarity)
        return best_type, results[best_type]
