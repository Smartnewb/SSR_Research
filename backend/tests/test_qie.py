"""Tests for QIE (Qualitative Insight Engine) functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.models.qie import (
    QIEJobStatus,
    SentimentCategory,
    KanoCategory,
    ImpactDirection,
    ActionPriority,
    Tier1Result,
    AggregatedStats,
    CategoryStats,
    KeyDriver,
    KanoFeature,
    KanoClassification,
    PainPoint,
    ActionItem,
    SegmentInsight,
    SegmentAnalysis,
    QIEAnalysis,
)
from backend.app.services.qie_pipeline import (
    QIEPipeline,
    tier1_result_to_dict,
    aggregated_stats_to_dict,
    qie_analysis_to_dict,
)


class TestQIEModels:
    """Tests for QIE data models."""

    def test_qie_job_status_enum(self):
        """Test QIEJobStatus enum values."""
        assert QIEJobStatus.PENDING.value == "pending"
        assert QIEJobStatus.TIER1_PROCESSING.value == "tier1_processing"
        assert QIEJobStatus.AGGREGATING.value == "aggregating"
        assert QIEJobStatus.TIER2_SYNTHESIS.value == "tier2_synthesis"
        assert QIEJobStatus.COMPLETED.value == "completed"
        assert QIEJobStatus.FAILED.value == "failed"

    def test_sentiment_category_enum(self):
        """Test SentimentCategory enum values."""
        assert SentimentCategory.PRICE.value == "Price"
        assert SentimentCategory.UX.value == "UX"
        assert SentimentCategory.TRUST.value == "Trust"
        assert SentimentCategory.FEATURE.value == "Feature"
        assert SentimentCategory.CONVENIENCE.value == "Convenience"
        assert SentimentCategory.OTHER.value == "Other"

    def test_kano_category_enum(self):
        """Test KanoCategory enum values."""
        assert KanoCategory.MUST_BE.value == "Must-be"
        assert KanoCategory.PERFORMANCE.value == "Performance"
        assert KanoCategory.DELIGHTER.value == "Delighter"
        assert KanoCategory.INDIFFERENT.value == "Indifferent"

    def test_tier1_result_creation(self):
        """Test Tier1Result dataclass creation."""
        result = Tier1Result(
            response_id="resp_001",
            sentiment=8,
            category=SentimentCategory.FEATURE,
            keywords=["quality", "price"],
            original_text="Great product!",
            ssr_score=0.8,
        )
        assert result.response_id == "resp_001"
        assert result.sentiment == 8
        assert result.category == SentimentCategory.FEATURE
        assert len(result.keywords) == 2

    def test_category_stats_creation(self):
        """Test CategoryStats dataclass creation."""
        stats = CategoryStats(
            category="Price",
            count=50,
            percentage=0.25,
            avg_sentiment=0.6,
            avg_ssr=0.55,
            top_keywords=["expensive", "value"],
        )
        assert stats.category == "Price"
        assert stats.count == 50
        assert stats.percentage == 0.25

    def test_aggregated_stats_creation(self):
        """Test AggregatedStats dataclass creation."""
        tier1_result = Tier1Result(
            response_id="p1",
            sentiment=3,
            category=SentimentCategory.PRICE,
            keywords=["expensive"],
            ssr_score=0.3,
        )
        category_stats = [
            CategoryStats(
                category="Price",
                count=50,
                percentage=0.25,
                avg_sentiment=0.6,
                avg_ssr=0.55,
                top_keywords=["expensive"],
            )
        ]
        stats = AggregatedStats(
            total_responses=200,
            avg_sentiment=0.65,
            sentiment_distribution={1: 10, 2: 20, 3: 50, 4: 80, 5: 40},
            category_stats=category_stats,
            keyword_frequency={"quality": 100, "price": 80},
            segment_breakdown={
                "age": {"20-30": {"count": 50, "avg_ssr": 0.7, "avg_sentiment": 0.65}}
            },
            low_ssr_responses=[tier1_result],
            high_ssr_responses=[],
        )
        assert stats.total_responses == 200
        assert stats.avg_sentiment == 0.65

    def test_key_driver_creation(self):
        """Test KeyDriver dataclass creation."""
        driver = KeyDriver(
            factor="Product Quality",
            impact=ImpactDirection.POSITIVE,
            correlation=0.85,
            description="High quality materials increase purchase intent",
            evidence_count=120,
            example_quotes=["Great quality!", "Well made"],
        )
        assert driver.factor == "Product Quality"
        assert driver.impact == ImpactDirection.POSITIVE
        assert driver.correlation == 0.85

    def test_kano_feature_creation(self):
        """Test KanoFeature dataclass creation."""
        feature = KanoFeature(
            feature_name="Fast Delivery",
            category=KanoCategory.MUST_BE,
            satisfaction_impact=0.9,
            mention_count=150,
            description="Expected feature that must be present",
        )
        assert feature.feature_name == "Fast Delivery"
        assert feature.category == KanoCategory.MUST_BE

    def test_pain_point_creation(self):
        """Test PainPoint dataclass creation."""
        pain = PainPoint(
            category=SentimentCategory.PRICE,
            score=0.8,
            description="Product is perceived as too expensive",
            affected_percentage=0.35,
            example_quotes=["Too expensive", "Not worth the price"],
        )
        assert pain.category == SentimentCategory.PRICE
        assert pain.score == 0.8
        assert pain.affected_percentage == 0.35

    def test_action_item_creation(self):
        """Test ActionItem dataclass creation."""
        action = ActionItem(
            title="Reduce pricing",
            description="Consider tiered pricing strategy",
            priority=ActionPriority.HIGH,
            category="Pricing",
            expected_impact="15% increase in conversion",
            related_pain_points=["Price too high"],
        )
        assert action.title == "Reduce pricing"
        assert action.priority == ActionPriority.HIGH


class TestQIESerializers:
    """Tests for QIE serialization helpers."""

    def test_tier1_result_to_dict(self):
        """Test Tier1Result serialization."""
        result = Tier1Result(
            response_id="resp_001",
            sentiment=8,
            category=SentimentCategory.FEATURE,
            keywords=["quality"],
            original_text="Good quality",
            ssr_score=0.8,
        )
        d = tier1_result_to_dict(result)
        assert d["response_id"] == "resp_001"
        assert d["sentiment"] == 8
        assert d["category"] == "Feature"

    def test_aggregated_stats_to_dict(self):
        """Test AggregatedStats serialization."""
        stats = AggregatedStats(
            total_responses=100,
            avg_sentiment=0.7,
            sentiment_distribution={3: 30, 4: 50, 5: 20},
            category_stats=[
                CategoryStats(
                    category="UX",
                    count=25,
                    percentage=0.25,
                    avg_sentiment=0.65,
                    avg_ssr=0.6,
                    top_keywords=["easy"],
                )
            ],
            keyword_frequency={"easy": 50},
            segment_breakdown={},
            low_ssr_responses=[],
            high_ssr_responses=[],
        )
        d = aggregated_stats_to_dict(stats)
        assert d["total_responses"] == 100
        assert d["avg_sentiment"] == 0.7
        assert len(d["category_stats"]) == 1
        assert d["category_stats"][0]["category"] == "UX"

    def test_qie_analysis_to_dict(self):
        """Test QIEAnalysis serialization."""
        analysis = QIEAnalysis(
            executive_summary="Test summary",
            key_drivers=[
                KeyDriver(
                    factor="Quality",
                    impact=ImpactDirection.POSITIVE,
                    correlation=0.8,
                    description="Test",
                    evidence_count=50,
                    example_quotes=[],
                )
            ],
            kano_classification=KanoClassification(
                must_be_features=[],
                performance_features=[],
                delighter_features=[],
                indifferent_features=[],
            ),
            segment_analysis=SegmentAnalysis(
                by_age=[],
                by_gender=[],
                by_income=[],
                notable_differences=[],
            ),
            pain_points=[],
            action_items=[],
            confidence_score=0.85,
            analysis_metadata={},
        )
        d = qie_analysis_to_dict(analysis)
        assert d["executive_summary"] == "Test summary"
        assert d["confidence_score"] == 0.85
        assert len(d["key_drivers"]) == 1
        assert d["key_drivers"][0]["impact"] == "positive"


class TestQIEPipeline:
    """Tests for QIEPipeline class."""

    @pytest.fixture
    def sample_responses(self):
        """Create sample survey responses for testing."""
        return [
            {
                "persona_id": "p1",
                "response_text": "I love this product! Great quality and reasonable price.",
                "ssr_score": 0.85,
                "demographics": {"age": 28, "gender": "female", "income": "mid"},
            },
            {
                "persona_id": "p2",
                "response_text": "Too expensive for what it offers.",
                "ssr_score": 0.35,
                "demographics": {"age": 45, "gender": "male", "income": "low"},
            },
            {
                "persona_id": "p3",
                "response_text": "Good product but delivery was slow.",
                "ssr_score": 0.65,
                "demographics": {"age": 32, "gender": "female", "income": "high"},
            },
        ]

    def test_pipeline_initialization(self):
        """Test QIEPipeline initialization."""
        pipeline = QIEPipeline()
        assert pipeline is not None
        assert pipeline.client is not None
        assert pipeline.tier1_semaphore is not None

    def test_pipeline_with_progress_callback(self):
        """Test QIEPipeline with progress callback."""
        callback = AsyncMock()
        pipeline = QIEPipeline(progress_callback=callback)
        assert pipeline.progress_callback == callback

    def test_aggregate_tier1_results(self, sample_responses):
        """Test Tier1 result aggregation."""
        pipeline = QIEPipeline()

        tier1_results = [
            Tier1Result(
                response_id="p1",
                sentiment=9,
                category=SentimentCategory.FEATURE,
                keywords=["quality", "price"],
                original_text="Great quality product",
                ssr_score=0.85,
            ),
            Tier1Result(
                response_id="p2",
                sentiment=3,
                category=SentimentCategory.PRICE,
                keywords=["expensive"],
                original_text="Too expensive",
                ssr_score=0.35,
            ),
            Tier1Result(
                response_id="p3",
                sentiment=6,
                category=SentimentCategory.CONVENIENCE,
                keywords=["delivery", "slow"],
                original_text="Delivery was slow",
                ssr_score=0.65,
            ),
        ]

        stats = pipeline.aggregate_tier1_results(tier1_results, sample_responses)

        assert stats.total_responses == 3
        assert 0 <= stats.avg_sentiment <= 10
        assert isinstance(stats.low_ssr_responses, list)
        assert isinstance(stats.high_ssr_responses, list)
        assert len(stats.category_stats) > 0


class TestQIEIntegration:
    """Integration tests for QIE pipeline (requires mocking OpenAI API)."""

    @pytest.fixture
    def mock_openai_response(self):
        """Create mock OpenAI API response."""
        mock_response = MagicMock()
        mock_response.output_text = """{
            "sentiment": 8,
            "category": "Feature",
            "keywords": ["quality", "design"]
        }"""
        return mock_response

    @pytest.mark.asyncio
    async def test_tier1_processing_with_mock(self, mock_openai_response):
        """Test Tier1 processing with mocked OpenAI response."""
        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.responses.create = AsyncMock(return_value=mock_openai_response)
            mock_client_class.return_value = mock_client

            pipeline = QIEPipeline()
            pipeline.client = mock_client

            responses = [
                {
                    "persona_id": "test_1",
                    "response_text": "Great product with good quality!",
                    "ssr_score": 0.8,
                    "demographics": {"age": 30, "gender": "male", "income": "mid"},
                }
            ]

            results = await pipeline.run_tier1_batch(responses)

            assert len(results) == 1
