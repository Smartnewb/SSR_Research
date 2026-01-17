"""Response validation for survey responses."""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


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
    "i cannot",
    "i can't actually",
    "i don't have personal",
    "i don't have preferences",
    "i'm not able to",
    "as a helpful assistant",
    "i am programmed",
    "my programming",
]


class ResponseIssueType(Enum):
    """Types of issues detected in LLM responses."""

    NONE = "none"
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    NUMERIC_RATING = "numeric_rating"
    CHARACTER_BREAK = "character_break"
    HALLUCINATION = "hallucination"
    EMPTY = "empty"
    GENERIC = "generic"


@dataclass
class ResponseValidationResult:
    """Detailed result of response validation."""

    is_valid: bool
    issue_type: ResponseIssueType
    message: str
    should_retry: bool
    confidence: float  # 0.0 = definitely invalid, 1.0 = definitely valid
    raw_response: str
    cleaned_response: Optional[str] = None


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


MIN_TOKEN_COUNT = 5
MAX_TOKEN_COUNT = 500
MIN_WORD_COUNT = 3


class ResponsePostProcessor:
    """
    Post-processor for LLM responses.

    Filters out hallucinations, character breaks, and invalid responses.
    Provides detailed validation results with retry recommendations.
    """

    def __init__(
        self,
        min_tokens: int = MIN_TOKEN_COUNT,
        max_tokens: int = MAX_TOKEN_COUNT,
        min_words: int = MIN_WORD_COUNT,
    ):
        """
        Initialize post-processor.

        Args:
            min_tokens: Minimum response length in tokens (approx words)
            max_tokens: Maximum response length in tokens
            min_words: Minimum word count
        """
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.min_words = min_words
        self.stats = {
            "total_processed": 0,
            "valid": 0,
            "invalid": 0,
            "retried": 0,
            "issues": {},
        }

    def process(self, response_text: str) -> ResponseValidationResult:
        """
        Process and validate a response.

        Args:
            response_text: Raw LLM response text

        Returns:
            ResponseValidationResult with detailed validation info
        """
        self.stats["total_processed"] += 1

        if not response_text or not response_text.strip():
            result = ResponseValidationResult(
                is_valid=False,
                issue_type=ResponseIssueType.EMPTY,
                message="Empty response received",
                should_retry=True,
                confidence=0.0,
                raw_response=response_text or "",
            )
            self._record_issue(result)
            return result

        cleaned = response_text.strip()
        word_count = len(cleaned.split())

        if word_count < self.min_words:
            result = ResponseValidationResult(
                is_valid=False,
                issue_type=ResponseIssueType.TOO_SHORT,
                message=f"Response too short: {word_count} words (min: {self.min_words})",
                should_retry=True,
                confidence=0.0,
                raw_response=response_text,
            )
            self._record_issue(result)
            logger.warning(f"TOO_SHORT: {word_count} words - '{cleaned[:50]}...'")
            return result

        if word_count > self.max_tokens:
            result = ResponseValidationResult(
                is_valid=False,
                issue_type=ResponseIssueType.TOO_LONG,
                message=f"Response too long: {word_count} words (max: {self.max_tokens})",
                should_retry=True,
                confidence=0.5,
                raw_response=response_text,
                cleaned_response=self._truncate(cleaned),
            )
            self._record_issue(result)
            logger.warning(f"TOO_LONG: {word_count} words")
            return result

        ai_phrase = self._detect_ai_phrase(cleaned)
        if ai_phrase:
            result = ResponseValidationResult(
                is_valid=False,
                issue_type=ResponseIssueType.CHARACTER_BREAK,
                message=f"Character break detected: '{ai_phrase}'",
                should_retry=True,
                confidence=0.0,
                raw_response=response_text,
            )
            self._record_issue(result)
            logger.warning(f"CHARACTER_BREAK: Found '{ai_phrase}'")
            return result

        numeric_match = self._detect_numeric_rating(cleaned)
        if numeric_match:
            result = ResponseValidationResult(
                is_valid=False,
                issue_type=ResponseIssueType.NUMERIC_RATING,
                message=f"Numeric rating found: '{numeric_match}'",
                should_retry=True,
                confidence=0.3,
                raw_response=response_text,
                cleaned_response=self._remove_numeric_rating(cleaned),
            )
            self._record_issue(result)
            logger.info(f"NUMERIC_RATING: '{numeric_match}' - may retry with reinforced prompt")
            return result

        if self._is_generic_response(cleaned):
            result = ResponseValidationResult(
                is_valid=False,
                issue_type=ResponseIssueType.GENERIC,
                message="Response appears too generic/template-like",
                should_retry=True,
                confidence=0.4,
                raw_response=response_text,
            )
            self._record_issue(result)
            return result

        self.stats["valid"] += 1
        return ResponseValidationResult(
            is_valid=True,
            issue_type=ResponseIssueType.NONE,
            message="Response validated successfully",
            should_retry=False,
            confidence=1.0,
            raw_response=response_text,
            cleaned_response=cleaned,
        )

    def _detect_ai_phrase(self, text: str) -> Optional[str]:
        """Detect AI self-reference phrases."""
        text_lower = text.lower()
        for phrase in AI_PHRASES:
            if phrase in text_lower:
                return phrase
        return None

    def _detect_numeric_rating(self, text: str) -> Optional[str]:
        """Detect numeric rating patterns."""
        for pattern in NUMERIC_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group()
        return None

    def _remove_numeric_rating(self, text: str) -> str:
        """Remove numeric ratings from text."""
        result = text
        for pattern in NUMERIC_PATTERNS:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)
        return result.strip()

    def _truncate(self, text: str, max_words: int = 200) -> str:
        """Truncate text to max words."""
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + "..."

    def _is_generic_response(self, text: str) -> bool:
        """Check if response is too generic."""
        generic_patterns = [
            r"^(yes|no|maybe|i think so|i don't think so)\.?$",
            r"^it depends\.?$",
            r"^(good|bad|okay|fine)\.?$",
        ]
        text_lower = text.lower().strip()
        for pattern in generic_patterns:
            if re.match(pattern, text_lower):
                return True
        return False

    def _record_issue(self, result: ResponseValidationResult) -> None:
        """Record issue statistics."""
        self.stats["invalid"] += 1
        issue_name = result.issue_type.value
        self.stats["issues"][issue_name] = self.stats["issues"].get(issue_name, 0) + 1

    def get_stats(self) -> dict:
        """Get processing statistics."""
        total = self.stats["total_processed"]
        return {
            **self.stats,
            "valid_rate": self.stats["valid"] / total if total > 0 else 0.0,
            "invalid_rate": self.stats["invalid"] / total if total > 0 else 0.0,
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = {
            "total_processed": 0,
            "valid": 0,
            "invalid": 0,
            "retried": 0,
            "issues": {},
        }
