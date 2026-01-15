"""Unit tests for survey module."""

import pytest

from src.survey.prompts import (
    create_survey_prompt,
    create_reinforced_prompt,
    create_full_prompt,
)
from src.survey.validator import (
    validate_llm_response,
    has_numeric_rating,
    has_ai_reference,
    extract_sentiment_indicators,
)
from src.survey.executor import (
    calculate_cost,
    CostTracker,
)


class TestCreateSurveyPrompt:
    """Tests for survey prompt creation."""

    def test_includes_product_description(self):
        """Should include product description."""
        prompt = create_survey_prompt("Amazing new smartphone")
        assert "Amazing new smartphone" in prompt

    def test_includes_no_rating_instruction(self):
        """Should include anti-numeric instruction."""
        prompt = create_survey_prompt("Test product")
        assert "Do NOT" in prompt or "numerical" in prompt.lower()

    def test_returns_string(self):
        """Should return string."""
        prompt = create_survey_prompt("Test")
        assert isinstance(prompt, str)


class TestCreateReinforcedPrompt:
    """Tests for reinforced prompt."""

    def test_includes_extra_instruction(self):
        """Should include reinforcement text."""
        prompt = create_reinforced_prompt("Test product")
        assert "Remember" in prompt or "Do NOT use numbers" in prompt

    def test_longer_than_basic(self):
        """Should be longer than basic prompt."""
        basic = create_survey_prompt("Test")
        reinforced = create_reinforced_prompt("Test")
        assert len(reinforced) > len(basic)


class TestCreateFullPrompt:
    """Tests for full prompt creation."""

    def test_combines_system_and_user(self):
        """Should combine system and user prompts."""
        full = create_full_prompt(
            "You are a 30-year-old designer.",
            "New design tool",
        )
        assert "30-year-old" in full
        assert "New design tool" in full

    def test_reinforced_flag(self):
        """Should use reinforced when flagged."""
        normal = create_full_prompt("System", "Product", reinforced=False)
        reinforced = create_full_prompt("System", "Product", reinforced=True)
        assert len(reinforced) > len(normal)


class TestValidateLLMResponse:
    """Tests for LLM response validation."""

    def test_valid_response(self):
        """Should accept valid response."""
        response = "I really like this product. It would fit my lifestyle well."
        is_valid, error = validate_llm_response(response)
        assert is_valid
        assert error == ""

    def test_empty_response(self):
        """Should reject empty response."""
        is_valid, error = validate_llm_response("")
        assert not is_valid
        assert "too short" in error.lower()

    def test_short_response(self):
        """Should reject very short response."""
        is_valid, error = validate_llm_response("Good.")
        assert not is_valid

    def test_numeric_rating_slash(self):
        """Should reject 4/5 format."""
        response = "I would rate this product 4/5."
        is_valid, error = validate_llm_response(response)
        assert not is_valid
        assert "numeric rating" in error.lower()

    def test_numeric_rating_out_of(self):
        """Should reject 'out of' format."""
        response = "I'd give this 8 out of 10."
        is_valid, error = validate_llm_response(response)
        assert not is_valid

    def test_numeric_rating_stars(self):
        """Should reject star ratings."""
        response = "This is a solid 4 stars product."
        is_valid, error = validate_llm_response(response)
        assert not is_valid

    def test_ai_reference(self):
        """Should reject AI self-reference."""
        response = "As an AI, I cannot have preferences."
        is_valid, error = validate_llm_response(response)
        assert not is_valid
        assert "AI" in error or "character" in error

    def test_language_model_reference(self):
        """Should reject language model reference."""
        response = "I am a language model and cannot purchase things."
        is_valid, error = validate_llm_response(response)
        assert not is_valid


class TestHasNumericRating:
    """Tests for numeric rating detection."""

    def test_detects_slash_format(self):
        """Should detect 4/5 format."""
        assert has_numeric_rating("I rate it 4/5")

    def test_detects_out_of(self):
        """Should detect 'out of' format."""
        assert has_numeric_rating("This is 7 out of 10")

    def test_detects_stars(self):
        """Should detect star rating."""
        assert has_numeric_rating("5 stars from me")

    def test_ignores_normal_numbers(self):
        """Should not flag normal number usage."""
        assert not has_numeric_rating("I bought 5 of these last year")

    def test_no_false_positive(self):
        """Should not flag clean response."""
        response = "I really love this product and would definitely buy it."
        assert not has_numeric_rating(response)


class TestHasAIReference:
    """Tests for AI reference detection."""

    def test_detects_as_an_ai(self):
        """Should detect 'as an AI'."""
        assert has_ai_reference("As an AI, I don't have needs.")

    def test_detects_language_model(self):
        """Should detect 'language model'."""
        assert has_ai_reference("I am a language model.")

    def test_case_insensitive(self):
        """Should be case insensitive."""
        assert has_ai_reference("AS AN AI...")

    def test_no_false_positive(self):
        """Should not flag clean response."""
        assert not has_ai_reference("I love this product!")


class TestExtractSentimentIndicators:
    """Tests for sentiment indicator extraction."""

    def test_positive_words(self):
        """Should count positive words."""
        indicators = extract_sentiment_indicators(
            "I love this amazing product! It's perfect for me."
        )
        assert indicators["positive_count"] >= 2

    def test_negative_words(self):
        """Should count negative words."""
        indicators = extract_sentiment_indicators(
            "This is terrible and useless. What a waste."
        )
        assert indicators["negative_count"] >= 2

    def test_word_count(self):
        """Should count total words."""
        indicators = extract_sentiment_indicators("one two three four five")
        assert indicators["word_count"] == 5

    def test_question_detection(self):
        """Should detect questions."""
        indicators = extract_sentiment_indicators("Is this any good?")
        assert indicators["has_question"]


class TestCalculateCost:
    """Tests for cost calculation."""

    def test_known_model(self):
        """Should calculate cost for known model."""
        usage = {"prompt_tokens": 100, "completion_tokens": 50}
        cost = calculate_cost("gpt-4o-mini", usage)
        assert cost > 0

    def test_unknown_model(self):
        """Should return 0 for unknown model."""
        usage = {"prompt_tokens": 100, "completion_tokens": 50}
        cost = calculate_cost("unknown-model", usage)
        assert cost == 0.0

    def test_cost_increases_with_tokens(self):
        """More tokens should cost more."""
        small_usage = {"prompt_tokens": 10, "completion_tokens": 10}
        large_usage = {"prompt_tokens": 1000, "completion_tokens": 1000}

        small_cost = calculate_cost("gpt-4o-mini", small_usage)
        large_cost = calculate_cost("gpt-4o-mini", large_usage)

        assert large_cost > small_cost


class TestCostTracker:
    """Tests for CostTracker class."""

    def test_initial_state(self):
        """Should start with zero cost."""
        tracker = CostTracker()
        assert tracker.total_cost == 0.0
        assert len(tracker.calls) == 0

    def test_record_call(self):
        """Should record API call."""
        tracker = CostTracker()
        tracker.record_call("gpt-4o-mini", {"tokens": 100}, 0.01)

        assert tracker.total_cost == 0.01
        assert len(tracker.calls) == 1

    def test_accumulate_cost(self):
        """Should accumulate costs."""
        tracker = CostTracker()
        tracker.record_call("gpt-4o-mini", {}, 0.01)
        tracker.record_call("gpt-4o-mini", {}, 0.02)
        tracker.record_call("gpt-4o-mini", {}, 0.03)

        assert tracker.total_cost == pytest.approx(0.06)

    def test_summary(self):
        """Should provide summary."""
        tracker = CostTracker()
        tracker.record_call("gpt-4o-mini", {}, 0.01)
        tracker.record_call("gpt-4o-mini", {}, 0.03)

        summary = tracker.summary()

        assert summary["total_cost"] == pytest.approx(0.04)
        assert summary["total_calls"] == 2
        assert summary["avg_cost_per_call"] == pytest.approx(0.02)

    def test_breakdown_by_model(self):
        """Should break down by model."""
        tracker = CostTracker()
        tracker.record_call("gpt-4o-mini", {}, 0.01)
        tracker.record_call("gpt-4o-mini", {}, 0.02)
        tracker.record_call("gpt-5-mini", {}, 0.05)

        summary = tracker.summary()
        breakdown = summary["breakdown"]

        assert breakdown["gpt-4o-mini"]["calls"] == 2
        assert breakdown["gpt-4o-mini"]["cost"] == pytest.approx(0.03)
        assert breakdown["gpt-5-mini"]["calls"] == 1

    def test_reset(self):
        """Should reset tracker."""
        tracker = CostTracker()
        tracker.record_call("model", {}, 0.01)
        tracker.reset()

        assert tracker.total_cost == 0.0
        assert len(tracker.calls) == 0
