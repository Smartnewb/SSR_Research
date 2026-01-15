"""SSR utility functions for vector operations."""

import numpy as np
from numpy.typing import NDArray


def cosine_similarity(vec_a: NDArray[np.float64], vec_b: NDArray[np.float64]) -> float:
    """
    Compute cosine similarity between two vectors.

    cos(θ) = (A · B) / (||A|| × ||B||)

    Args:
        vec_a: First vector (1D numpy array)
        vec_b: Second vector (1D numpy array)

    Returns:
        Cosine similarity in range [-1, 1]:
        - 1.0 = identical direction
        - 0.0 = orthogonal
        - -1.0 = opposite direction
    """
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


def normalize_to_unit(score: float, min_val: float = -1.0, max_val: float = 1.0) -> float:
    """
    Normalize a value from [min_val, max_val] to [0, 1].

    Args:
        score: Value to normalize
        min_val: Minimum of input range (default: -1.0 for cosine similarity)
        max_val: Maximum of input range (default: 1.0 for cosine similarity)

    Returns:
        Normalized value in [0, 1]
    """
    return (score - min_val) / (max_val - min_val)


def to_likert_5(ssr_score: float) -> float:
    """Convert SSR score [0, 1] to 1-5 Likert scale."""
    return 1 + (ssr_score * 4)


def to_percentage(ssr_score: float) -> float:
    """Convert SSR score [0, 1] to 0-100 percentage."""
    return ssr_score * 100


def to_scale_10(ssr_score: float) -> float:
    """Convert SSR score [0, 1] to 0-10 scale."""
    return ssr_score * 10
