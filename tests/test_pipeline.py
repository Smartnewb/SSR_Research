"""End-to-end tests for SSR pipeline."""

import numpy as np
import pytest

from src.pipeline import SSRPipeline
from src.reporting.aggregator import AggregatedResults


class TestSSRPipelineMock:
    """E2E tests using mock data (no API calls)."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance."""
        return SSRPipeline()

    def test_mock_survey_returns_results(self, pipeline):
        """Should return aggregated results from mock survey."""
        result = pipeline.run_survey_mock(
            product_description="Test product",
            sample_size=10,
        )

        assert isinstance(result, AggregatedResults)
        assert result.sample_size == 10

    def test_mock_survey_scores_in_range(self, pipeline):
        """All scores should be in [0, 1] range."""
        result = pipeline.run_survey_mock(
            product_description="Test product",
            sample_size=20,
        )

        for survey_result in result.results:
            assert 0.0 <= survey_result.ssr_score <= 1.0

    def test_mock_survey_has_personas(self, pipeline):
        """Each result should have persona data."""
        result = pipeline.run_survey_mock(
            product_description="Test product",
            sample_size=10,
        )

        for survey_result in result.results:
            assert survey_result.persona_id is not None
            assert survey_result.persona_data is not None
            assert "age" in survey_result.persona_data

    def test_mock_survey_has_responses(self, pipeline):
        """Each result should have response text."""
        result = pipeline.run_survey_mock(
            product_description="Test product",
            sample_size=10,
        )

        for survey_result in result.results:
            assert survey_result.response_text is not None
            assert len(survey_result.response_text) > 0

    def test_mock_survey_varied_responses(self, pipeline):
        """Varied responses should produce varied scores."""
        varied_responses = [
            "I absolutely love this! Must buy immediately!",
            "This is exactly what I need, definitely purchasing.",
            "Seems interesting, might consider it.",
            "Not sure if this is for me, maybe later.",
            "I don't think I need this at all.",
            "This is completely useless, waste of money.",
        ]

        result = pipeline.run_survey_mock(
            product_description="Test product",
            sample_size=6,
            mock_responses=varied_responses,
        )

        scores = [r.ssr_score for r in result.results]
        std_dev = np.std(scores)

        # Mock embeddings have lower variance than real ones
        # Just verify scores are not all identical
        assert std_dev > 0.001, f"Scores too uniform: std={std_dev:.4f}"
        assert not all(s == scores[0] for s in scores), "All scores identical"

    def test_mock_survey_statistics(self, pipeline):
        """Should calculate correct statistics."""
        result = pipeline.run_survey_mock(
            product_description="Test product",
            sample_size=20,
        )

        assert result.mean_score >= 0.0
        assert result.mean_score <= 1.0
        assert result.median_score >= 0.0
        assert result.median_score <= 1.0
        assert result.std_dev >= 0.0
        assert result.min_score >= 0.0
        assert result.max_score <= 1.0

    def test_mock_survey_distribution(self, pipeline):
        """Should generate score distribution."""
        result = pipeline.run_survey_mock(
            product_description="Test product",
            sample_size=50,
        )

        assert result.score_distribution is not None
        assert len(result.score_distribution) > 0

        total_count = sum(result.score_distribution.values())
        assert total_count == 50


class TestSSRPipelineIntegration:
    """Integration tests (require API key - skip if not available)."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance."""
        return SSRPipeline(llm_model="gpt-4o-mini")

    @pytest.mark.skip(reason="Requires OpenAI API key")
    def test_real_survey_small(self, pipeline):
        """Test real survey with small sample (costs ~$0.05)."""
        result = pipeline.run_survey(
            product_description="A smart coffee mug that keeps drinks at perfect temperature",
            sample_size=5,
        )

        assert result.sample_size == 5
        assert result.total_cost > 0
        assert result.total_cost < 0.10

        for survey_result in result.results:
            assert 0.0 <= survey_result.ssr_score <= 1.0


class TestPipelineStats:
    """Tests for pipeline statistics."""

    def test_stats_after_mock_survey(self):
        """Should track stats after mock survey."""
        pipeline = SSRPipeline()
        pipeline.run_survey_mock("Test", sample_size=5)

        stats = pipeline.stats
        assert "initialized" in stats
        assert "cost_summary" in stats

    def test_reset_clears_stats(self):
        """Should clear stats on reset."""
        pipeline = SSRPipeline()
        pipeline.run_survey_mock("Test", sample_size=5)
        pipeline.reset()

        stats = pipeline.stats
        assert stats["cost_summary"]["total_cost"] == 0.0
