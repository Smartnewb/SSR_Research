"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_survey_request():
    """Sample survey request for testing."""
    return {
        "product_description": "A smart coffee mug that keeps your drink at the perfect temperature. Price: $79.",
        "sample_size": 10,
        "use_mock": True,
        "model": "gpt-4o-mini",
    }


@pytest.fixture
def mock_ab_test_request():
    """Sample A/B test request for testing."""
    return {
        "product_a": "Smart coffee mug with temperature control - $79",
        "product_b": "Regular insulated mug - $15",
        "product_a_name": "Smart Mug",
        "product_b_name": "Regular Mug",
        "sample_size": 10,
        "use_mock": True,
        "model": "gpt-4o-mini",
    }
