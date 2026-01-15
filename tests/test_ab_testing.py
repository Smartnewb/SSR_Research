"""Tests for A/B testing module."""

import pytest
import numpy as np

from src.ab_testing import (
    ABTestResult,
    calculate_cohens_d,
    run_ab_test,
    run_ab_test_mock,
)


class TestCohensD:
    """Tests for Cohen's d effect size calculation."""

    def test_zero_difference(self):
        """Same means should give zero effect size."""
        d = calculate_cohens_d(0.5, 0.5, 0.1, 0.1)
        assert d == 0.0

    def test_positive_difference(self):
        """Higher mean A should give positive effect size."""
        d = calculate_cohens_d(0.7, 0.5, 0.1, 0.1)
        assert d > 0

    def test_negative_difference(self):
        """Lower mean A should give negative effect size."""
        d = calculate_cohens_d(0.3, 0.5, 0.1, 0.1)
        assert d < 0

    def test_large_effect(self):
        """Large difference should give large effect size."""
        d = calculate_cohens_d(0.9, 0.1, 0.1, 0.1)
        assert abs(d) > 0.8

    def test_zero_std(self):
        """Zero standard deviation should return 0."""
        d = calculate_cohens_d(0.5, 0.3, 0.0, 0.0)
        assert d == 0.0


class TestABTestResult:
    """Tests for ABTestResult dataclass."""

    @pytest.fixture
    def mock_ab_result(self):
        """Create a mock A/B test result."""
        return run_ab_test_mock(
            product_a="Product A description",
            product_b="Product B description",
            sample_size=10,
            product_a_name="Smart Mug",
            product_b_name="Regular Mug",
        )

    def test_has_product_names(self, mock_ab_result):
        """Result should contain product names."""
        assert mock_ab_result.product_a_name == "Smart Mug"
        assert mock_ab_result.product_b_name == "Regular Mug"

    def test_has_results(self, mock_ab_result):
        """Result should contain aggregated results for both products."""
        assert mock_ab_result.results_a is not None
        assert mock_ab_result.results_b is not None
        assert mock_ab_result.results_a.sample_size == 10
        assert mock_ab_result.results_b.sample_size == 10

    def test_has_statistics(self, mock_ab_result):
        """Result should contain statistical measures."""
        assert isinstance(mock_ab_result.mean_difference, float)
        assert isinstance(mock_ab_result.t_statistic, float)
        assert isinstance(mock_ab_result.p_value, float)
        assert isinstance(mock_ab_result.effect_size, float)

    def test_confidence_interval(self, mock_ab_result):
        """Confidence interval should be a tuple of two floats."""
        assert isinstance(mock_ab_result.confidence_interval, tuple)
        assert len(mock_ab_result.confidence_interval) == 2
        lower, upper = mock_ab_result.confidence_interval
        assert lower <= upper

    def test_p_value_range(self, mock_ab_result):
        """P-value should be between 0 and 1."""
        assert 0 <= mock_ab_result.p_value <= 1

    def test_effect_size_non_negative(self, mock_ab_result):
        """Effect size should be non-negative."""
        assert mock_ab_result.effect_size >= 0

    def test_significant_has_winner(self, mock_ab_result):
        """If significant, winner should be set."""
        if mock_ab_result.significant:
            assert mock_ab_result.winner in [
                mock_ab_result.product_a_name,
                mock_ab_result.product_b_name,
            ]

    def test_not_significant_no_winner(self, mock_ab_result):
        """If not significant, winner should be None."""
        if not mock_ab_result.significant:
            assert mock_ab_result.winner is None


class TestABTestResultMethods:
    """Tests for ABTestResult methods."""

    @pytest.fixture
    def mock_ab_result(self):
        """Create a mock A/B test result."""
        return run_ab_test_mock(
            product_a="Test product A",
            product_b="Test product B",
            sample_size=15,
        )

    def test_summary_returns_string(self, mock_ab_result):
        """Summary should return a formatted string."""
        summary = mock_ab_result.summary()
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_summary_contains_product_names(self, mock_ab_result):
        """Summary should contain product names."""
        summary = mock_ab_result.summary()
        assert "Product A" in summary
        assert "Product B" in summary

    def test_summary_contains_statistics(self, mock_ab_result):
        """Summary should contain key statistics."""
        summary = mock_ab_result.summary()
        assert "Mean Score" in summary
        assert "p-value" in summary
        assert "Effect Size" in summary

    def test_to_dict_returns_dict(self, mock_ab_result):
        """to_dict should return a dictionary."""
        data = mock_ab_result.to_dict()
        assert isinstance(data, dict)

    def test_to_dict_has_products(self, mock_ab_result):
        """Dictionary should have product data."""
        data = mock_ab_result.to_dict()
        assert "product_a" in data
        assert "product_b" in data
        assert "name" in data["product_a"]
        assert "mean_score" in data["product_a"]

    def test_to_dict_has_analysis(self, mock_ab_result):
        """Dictionary should have analysis data."""
        data = mock_ab_result.to_dict()
        assert "analysis" in data
        assert "t_statistic" in data["analysis"]
        assert "p_value" in data["analysis"]
        assert "significant" in data["analysis"]


class TestRunABTest:
    """Tests for run_ab_test function."""

    def test_mock_mode_works(self):
        """A/B test should work in mock mode."""
        result = run_ab_test(
            product_a="Test A",
            product_b="Test B",
            sample_size=10,
            use_mock=True,
            show_progress=False,
        )
        assert isinstance(result, ABTestResult)

    def test_custom_names(self):
        """Custom product names should be preserved."""
        result = run_ab_test(
            product_a="Test A",
            product_b="Test B",
            sample_size=10,
            product_a_name="Premium",
            product_b_name="Budget",
            use_mock=True,
            show_progress=False,
        )
        assert result.product_a_name == "Premium"
        assert result.product_b_name == "Budget"

    def test_sample_size_respected(self):
        """Sample size should match requested value."""
        result = run_ab_test(
            product_a="Test A",
            product_b="Test B",
            sample_size=25,
            use_mock=True,
            show_progress=False,
        )
        assert result.results_a.sample_size == 25
        assert result.results_b.sample_size == 25

    def test_mean_difference_calculated(self):
        """Mean difference should be calculated correctly."""
        result = run_ab_test(
            product_a="Test A",
            product_b="Test B",
            sample_size=20,
            use_mock=True,
            show_progress=False,
        )
        expected_diff = result.results_a.mean_score - result.results_b.mean_score
        assert abs(result.mean_difference - expected_diff) < 1e-9


class TestRunABTestMock:
    """Tests for run_ab_test_mock convenience function."""

    def test_returns_ab_result(self):
        """Should return ABTestResult."""
        result = run_ab_test_mock(
            product_a="Test A",
            product_b="Test B",
        )
        assert isinstance(result, ABTestResult)

    def test_default_sample_size(self):
        """Default sample size should be 20."""
        result = run_ab_test_mock(
            product_a="Test A",
            product_b="Test B",
        )
        assert result.results_a.sample_size == 20
        assert result.results_b.sample_size == 20

    def test_custom_product_names(self):
        """Custom product names should be set."""
        result = run_ab_test_mock(
            product_a="Test A",
            product_b="Test B",
            product_a_name="Alpha",
            product_b_name="Beta",
        )
        assert result.product_a_name == "Alpha"
        assert result.product_b_name == "Beta"
