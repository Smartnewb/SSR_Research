"""SSR (Semantic Similarity Rating) calculation module."""

from .calculator import SSRCalculator
from .utils import cosine_similarity, to_likert_5, to_percentage, to_scale_10
from .anchors import POSITIVE_ANCHOR, NEGATIVE_ANCHOR, get_anchors

__all__ = [
    "SSRCalculator",
    "cosine_similarity",
    "to_likert_5",
    "to_percentage",
    "to_scale_10",
    "POSITIVE_ANCHOR",
    "NEGATIVE_ANCHOR",
    "get_anchors",
]
