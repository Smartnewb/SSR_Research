"""Unit tests for reporting module."""

import pytest

from src.reporting.aggregator import (
    SurveyResult,
    AggregatedResults,
    aggregate_results,
    calculate_statistics,
    calculate_distribution,
    get_top_responses,
    format_summary_text,
)


class TestSurveyResult:
    """Tests for SurveyResult dataclass."""

    def test_creation(self):
        """Should create result with required fields."""
        result = SurveyResult(
            persona_id="test-001",
            response_text="I love this product.",
            ssr_score=0.8,
        )
        assert result.persona_id == "test-001"
        assert result.ssr_score == 0.8

    def test_defaults(self):
        """Should have sensible defaults."""
        result = SurveyResult(
            persona_id="test",
            response_text="Test",
            ssr_score=0.5,
        )
        assert result.tokens_used == 0
        assert result.cost == 0.0


class TestCalculateStatistics:
    """Tests for calculate_statistics function."""

    def test_empty_list(self):
        """Should handle empty list."""
        stats = calculate_statistics([])
        assert stats["mean"] == 0.0
        assert stats["std_dev"] == 0.0

    def test_single_value(self):
        """Should handle single value."""
        stats = calculate_statistics([0.5])
        assert stats["mean"] == pytest.approx(0.5)
        assert stats["std_dev"] == 0.0

    def test_known_values(self):
        """Should calculate correct statistics."""
        scores = [0.2, 0.4, 0.6, 0.8, 1.0]
        stats = calculate_statistics(scores)

        assert stats["mean"] == pytest.approx(0.6)
        assert stats["median"] == pytest.approx(0.6)
        assert stats["min"] == pytest.approx(0.2)
        assert stats["max"] == pytest.approx(1.0)
        assert stats["std_dev"] > 0


class TestCalculateDistribution:
    """Tests for calculate_distribution function."""

    def test_empty_list(self):
        """Should handle empty list."""
        dist = calculate_distribution([])
        assert dist == {}

    def test_creates_bins(self):
        """Should create histogram bins."""
        scores = [0.1, 0.3, 0.5, 0.7, 0.9]
        dist = calculate_distribution(scores, bins=5)

        assert len(dist) == 5
        assert sum(dist.values()) == 5

    def test_bin_labels(self):
        """Should have correct bin labels."""
        dist = calculate_distribution([0.5], bins=10)
        labels = list(dist.keys())
        assert any("0.4" in l and "0.5" in l for l in labels)


class TestAggregateResults:
    """Tests for aggregate_results function."""

    def test_empty_results(self):
        """Should handle empty results."""
        agg = aggregate_results([])
        assert agg.sample_size == 0
        assert agg.mean_score == 0.0

    def test_aggregation(self):
        """Should aggregate results correctly."""
        results = [
            SurveyResult("p1", "Good", 0.8, cost=0.01, tokens_used=100),
            SurveyResult("p2", "Bad", 0.2, cost=0.01, tokens_used=100),
            SurveyResult("p3", "OK", 0.5, cost=0.01, tokens_used=100),
        ]

        agg = aggregate_results(results)

        assert agg.sample_size == 3
        assert agg.mean_score == pytest.approx(0.5)
        assert agg.total_cost == pytest.approx(0.03)
        assert agg.total_tokens == 300

    def test_to_dict(self):
        """Should convert to dictionary."""
        results = [SurveyResult("p1", "Test", 0.5)]
        agg = aggregate_results(results)

        d = agg.to_dict()

        assert "mean_score" in d
        assert "sample_size" in d


class TestGetTopResponses:
    """Tests for get_top_responses function."""

    def test_gets_highest(self):
        """Should get highest scoring responses."""
        results = [
            SurveyResult("p1", "Low", 0.2),
            SurveyResult("p2", "High", 0.9),
            SurveyResult("p3", "Mid", 0.5),
        ]

        top = get_top_responses(results, n=2, high=True)

        assert len(top) == 2
        assert top[0].ssr_score == 0.9
        assert top[1].ssr_score == 0.5

    def test_gets_lowest(self):
        """Should get lowest scoring responses."""
        results = [
            SurveyResult("p1", "Low", 0.2),
            SurveyResult("p2", "High", 0.9),
            SurveyResult("p3", "Mid", 0.5),
        ]

        bottom = get_top_responses(results, n=2, high=False)

        assert len(bottom) == 2
        assert bottom[0].ssr_score == 0.2
        assert bottom[1].ssr_score == 0.5


class TestFormatSummaryText:
    """Tests for format_summary_text function."""

    def test_includes_key_metrics(self):
        """Should include key metrics."""
        results = [SurveyResult("p1", "Test", 0.75)]
        agg = aggregate_results(results)

        text = format_summary_text(agg)

        assert "Sample Size" in text
        assert "Mean Score" in text
        assert "Total Cost" in text

    def test_readable_format(self):
        """Should be human readable."""
        results = [SurveyResult("p1", "Test", 0.5, cost=0.01)]
        agg = aggregate_results(results)

        text = format_summary_text(agg)

        assert "=" in text
        assert len(text) > 100
