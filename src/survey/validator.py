"""Response validation for survey responses."""

import re


NUMERIC_PATTERNS = [
    r'\d+\s*out of\s*\d+',
    r'\d+/\d+',
    r'rating:?\s*\d+',
    r'score:?\s*\d+',
    r'\d+\s*stars?',
    r'\b[1-9]0?\s*(?:out of|\/)\s*10\b',
    r'\brate\s+(?:it\s+)?(?:a\s+)?\d+\b',
]


AI_PHRASES = [
    "as an ai",
    "i am an ai",
    "i'm an ai",
    "language model",
    "as a language model",
    "as an artificial",
]


def validate_llm_response(response_text: str) -> tuple[bool, str]:
    """
    Validate that LLM response is suitable for SSR.

    Invalid responses:
    - Contains explicit numeric ratings ("4/5", "7 out of 10")
    - Too short (<10 characters)
    - Empty
    - Breaks character ("As an AI...")

    Args:
        response_text: LLM response to validate

    Returns:
        (is_valid, error_message)
    """
    if not response_text or len(response_text.strip()) < 10:
        return False, "Response too short or empty"

    for pattern in NUMERIC_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            return False, f"Response contains numeric rating matching: {pattern}"

    response_lower = response_text.lower()
    for phrase in AI_PHRASES:
        if phrase in response_lower:
            return False, "Response breaks character (AI self-reference)"

    return True, ""


def has_numeric_rating(response_text: str) -> bool:
    """
    Check if response contains numeric rating.

    Args:
        response_text: Response to check

    Returns:
        True if numeric rating found
    """
    for pattern in NUMERIC_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            return True
    return False


def has_ai_reference(response_text: str) -> bool:
    """
    Check if response contains AI self-reference.

    Args:
        response_text: Response to check

    Returns:
        True if AI reference found
    """
    response_lower = response_text.lower()
    return any(phrase in response_lower for phrase in AI_PHRASES)


def extract_sentiment_indicators(response_text: str) -> dict:
    """
    Extract basic sentiment indicators from response.

    Args:
        response_text: Response to analyze

    Returns:
        Dictionary with sentiment indicators
    """
    text_lower = response_text.lower()

    positive_words = [
        "love", "great", "excellent", "amazing", "perfect", "fantastic",
        "wonderful", "definitely", "absolutely", "must-have", "need",
        "excited", "interested", "useful", "helpful", "convenient",
    ]

    negative_words = [
        "hate", "terrible", "awful", "horrible", "waste", "useless",
        "expensive", "overpriced", "unnecessary", "don't need", "won't buy",
        "no way", "never", "disappointed", "skeptical", "doubt",
    ]

    neutral_words = [
        "maybe", "perhaps", "depends", "not sure", "uncertain",
        "could be", "might", "okay", "fine", "average",
    ]

    positive_count = sum(1 for w in positive_words if w in text_lower)
    negative_count = sum(1 for w in negative_words if w in text_lower)
    neutral_count = sum(1 for w in neutral_words if w in text_lower)

    return {
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "word_count": len(response_text.split()),
        "has_question": "?" in response_text,
    }
