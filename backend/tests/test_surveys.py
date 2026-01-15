"""Tests for survey API endpoints."""

import pytest


def test_run_survey_mock(client, mock_survey_request):
    """Test running a survey with mock data."""
    response = client.post("/api/surveys", json=mock_survey_request)
    assert response.status_code == 200

    data = response.json()
    assert "survey_id" in data
    assert data["sample_size"] == mock_survey_request["sample_size"]
    assert "mean_score" in data
    assert 0 <= data["mean_score"] <= 1
    assert "std_dev" in data
    assert "results" in data
    assert len(data["results"]) == mock_survey_request["sample_size"]


def test_run_survey_validation_error(client):
    """Test survey endpoint rejects invalid requests."""
    invalid_request = {
        "product_description": "short",
        "sample_size": 10,
        "use_mock": True,
    }

    response = client.post("/api/surveys", json=invalid_request)
    assert response.status_code == 422


def test_run_survey_sample_size_limits(client):
    """Test survey endpoint enforces sample size limits."""
    too_small = {
        "product_description": "A smart coffee mug that keeps your drink hot",
        "sample_size": 2,
        "use_mock": True,
    }
    response = client.post("/api/surveys", json=too_small)
    assert response.status_code == 422

    too_large = {
        "product_description": "A smart coffee mug that keeps your drink hot",
        "sample_size": 500,
        "use_mock": True,
    }
    response = client.post("/api/surveys", json=too_large)
    assert response.status_code == 422


def test_run_survey_with_demographics(client):
    """Test running a survey with demographic filters."""
    request = {
        "product_description": "A smart coffee mug that keeps your drink at the perfect temperature.",
        "sample_size": 10,
        "use_mock": True,
        "demographics": {
            "age_range": [25, 45],
            "gender": ["Male", "Female"],
        },
    }

    response = client.post("/api/surveys", json=request)
    assert response.status_code == 200

    data = response.json()
    assert len(data["results"]) == 10


def test_run_ab_test_mock(client, mock_ab_test_request):
    """Test running an A/B test with mock data."""
    response = client.post("/api/surveys/compare", json=mock_ab_test_request)
    assert response.status_code == 200

    data = response.json()
    assert "test_id" in data
    assert data["product_a_name"] == mock_ab_test_request["product_a_name"]
    assert data["product_b_name"] == mock_ab_test_request["product_b_name"]
    assert "results_a" in data
    assert "results_b" in data
    assert "statistics" in data

    stats = data["statistics"]
    assert "mean_difference" in stats
    assert "p_value" in stats
    assert "effect_size" in stats
    assert "significant" in stats


def test_run_ab_test_validation_error(client):
    """Test A/B test endpoint rejects invalid requests."""
    invalid_request = {
        "product_a": "short",
        "product_b": "also short",
        "sample_size": 10,
        "use_mock": True,
    }

    response = client.post("/api/surveys/compare", json=invalid_request)
    assert response.status_code == 422


def test_survey_result_structure(client, mock_survey_request):
    """Test survey result contains all expected fields."""
    response = client.post("/api/surveys", json=mock_survey_request)
    assert response.status_code == 200

    data = response.json()

    required_fields = [
        "survey_id",
        "product_description",
        "sample_size",
        "mean_score",
        "median_score",
        "std_dev",
        "min_score",
        "max_score",
        "score_distribution",
        "total_cost",
        "total_tokens",
        "execution_time_seconds",
        "results",
        "created_at",
    ]

    for field in required_fields:
        assert field in data, f"Missing field: {field}"


def test_survey_result_item_structure(client, mock_survey_request):
    """Test individual result items have correct structure."""
    response = client.post("/api/surveys", json=mock_survey_request)
    assert response.status_code == 200

    data = response.json()
    result = data["results"][0]

    required_fields = [
        "persona_id",
        "ssr_score",
        "likert_5",
        "scale_10",
        "response_text",
    ]

    for field in required_fields:
        assert field in result, f"Missing field: {field}"

    assert 0 <= result["ssr_score"] <= 1
    assert 1 <= result["likert_5"] <= 5
    assert 1 <= result["scale_10"] <= 10


def test_export_not_implemented(client):
    """Test export endpoint returns 501 (not implemented)."""
    response = client.get("/api/surveys/fake_id/export")
    assert response.status_code == 501
