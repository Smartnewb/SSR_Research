"""Semantic anchor text definitions for SSR calculation."""

POSITIVE_ANCHOR = "I would definitely buy this product."
NEGATIVE_ANCHOR = "I would never buy this product."

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
