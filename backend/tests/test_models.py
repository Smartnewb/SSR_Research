"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from backend.app.models.request import SurveyRequest, ABTestRequest, DemographicsFilter
from backend.app.models.response import SurveyResponse, SurveyResultItem


class TestSurveyRequest:
    """Tests for SurveyRequest model."""

    def test_valid_request(self):
        """Test valid survey request."""
        request = SurveyRequest(
            product_description="A smart coffee mug that keeps your drink hot",
            sample_size=20,
            use_mock=True,
        )
        assert request.sample_size == 20
        assert request.use_mock is True

    def test_default_values(self):
        """Test default values are applied."""
        request = SurveyRequest(
            product_description="A smart coffee mug that keeps your drink hot",
        )
        assert request.sample_size == 20
        assert request.use_mock is False
        assert request.model == "gpt-4o-mini"

    def test_product_description_min_length(self):
        """Test product description minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            SurveyRequest(product_description="short")
        assert "product_description" in str(exc_info.value)

    def test_sample_size_range(self):
        """Test sample size range validation."""
        with pytest.raises(ValidationError):
            SurveyRequest(
                product_description="A smart coffee mug that keeps your drink hot",
                sample_size=3,
            )

        with pytest.raises(ValidationError):
            SurveyRequest(
                product_description="A smart coffee mug that keeps your drink hot",
                sample_size=300,
            )


class TestDemographicsFilter:
    """Tests for DemographicsFilter model."""

    def test_valid_demographics(self):
        """Test valid demographics filter."""
        demo = DemographicsFilter(
            age_range=(25, 45),
            gender=["Male", "Female"],
            income_bracket=["Middle", "High"],
        )
        assert demo.age_range == (25, 45)
        assert demo.gender == ["Male", "Female"]

    def test_age_range_validation(self):
        """Test age range validation."""
        with pytest.raises(ValidationError):
            DemographicsFilter(age_range=(10, 30))

        with pytest.raises(ValidationError):
            DemographicsFilter(age_range=(25, 90))

        with pytest.raises(ValidationError):
            DemographicsFilter(age_range=(50, 30))


class TestABTestRequest:
    """Tests for ABTestRequest model."""

    def test_valid_request(self):
        """Test valid A/B test request."""
        request = ABTestRequest(
            product_a="Smart mug with temperature control - $79",
            product_b="Regular insulated mug - $15",
            product_a_name="Smart Mug",
            product_b_name="Regular Mug",
            sample_size=30,
            use_mock=True,
        )
        assert request.product_a_name == "Smart Mug"
        assert request.sample_size == 30

    def test_default_names(self):
        """Test default product names."""
        request = ABTestRequest(
            product_a="Smart mug with temperature control - $79",
            product_b="Regular insulated mug - $15",
        )
        assert request.product_a_name == "Product A"
        assert request.product_b_name == "Product B"


class TestSurveyResultItem:
    """Tests for SurveyResultItem model."""

    def test_valid_result_item(self):
        """Test valid survey result item."""
        item = SurveyResultItem(
            persona_id="persona_001",
            ssr_score=0.65,
            likert_5=3.6,
            scale_10=7.0,
            response_text="I would consider buying this product.",
        )
        assert item.ssr_score == 0.65
        assert item.likert_5 == 3.6

    def test_score_range_validation(self):
        """Test SSR score range validation."""
        with pytest.raises(ValidationError):
            SurveyResultItem(
                persona_id="persona_001",
                ssr_score=1.5,
                likert_5=3.6,
                scale_10=7.0,
                response_text="Test",
            )

        with pytest.raises(ValidationError):
            SurveyResultItem(
                persona_id="persona_001",
                ssr_score=-0.1,
                likert_5=3.6,
                scale_10=7.0,
                response_text="Test",
            )
