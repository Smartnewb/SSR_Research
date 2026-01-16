"""Tests for persona generation API endpoints."""

import pytest


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from backend.app.main import app
    return TestClient(app)


@pytest.fixture
def core_persona_id(client):
    """Create a core persona for testing."""
    response = client.post(
        "/api/personas/core",
        json={
            "name": "Generation Test Persona",
            "age_range": [30, 40],
            "gender_distribution": {"female": 60, "male": 40},
            "income_brackets": {"low": 20, "mid": 60, "high": 20},
            "location": "urban",
            "category_usage": "high",
            "shopping_behavior": "smart_shopper",
            "key_pain_points": ["high prices", "poor quality"],
            "decision_drivers": ["value", "reviews"]
        }
    )
    return response.json()["id"]


class TestGeneratePersonas:
    """Tests for POST /api/personas/generate."""

    def test_generate_personas_with_id(self, client, core_persona_id):
        """Test generating personas with core persona ID."""
        response = client.post(
            "/api/personas/generate",
            json={
                "core_persona_id": core_persona_id,
                "sample_size": 50,
                "random_seed": 42
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["total_personas"] == 50
        assert "personas" in data
        assert len(data["personas"]) == 50

    def test_generate_personas_with_config(self, client):
        """Test generating personas with direct config."""
        response = client.post(
            "/api/personas/generate",
            json={
                "core_config": {
                    "age_range": [25, 35],
                    "gender_distribution": {"female": 50, "male": 50},
                    "income_brackets": {"low": 30, "mid": 50, "high": 20},
                    "location": "urban",
                    "category_usage": "medium",
                    "shopping_behavior": "budget",
                    "key_pain_points": ["test"],
                    "decision_drivers": ["price"]
                },
                "sample_size": 20,
                "random_seed": 123
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_personas"] == 20

    def test_generate_personas_min_size(self, client, core_persona_id):
        """Test with minimum sample size."""
        response = client.post(
            "/api/personas/generate",
            json={
                "core_persona_id": core_persona_id,
                "sample_size": 5
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_personas"] == 5

    def test_generate_personas_invalid_core(self, client):
        """Test with non-existent core persona."""
        response = client.post(
            "/api/personas/generate",
            json={
                "core_persona_id": "NONEXISTENT_ID",
                "sample_size": 100
            }
        )
        assert response.status_code == 404

    def test_generate_personas_no_config(self, client):
        """Test without providing either ID or config."""
        response = client.post(
            "/api/personas/generate",
            json={
                "sample_size": 100
            }
        )
        assert response.status_code == 400

    def test_generate_personas_distribution(self, client, core_persona_id):
        """Test that generated personas follow expected distribution."""
        response = client.post(
            "/api/personas/generate",
            json={
                "core_persona_id": core_persona_id,
                "sample_size": 100,
                "random_seed": 42
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        personas = data["personas"]
        ages = [p["age"] for p in personas]
        
        # Check age distribution is within range
        assert all(30 <= age <= 40 for age in ages)


class TestPreviewPersonas:
    """Tests for GET /api/personas/preview."""

    def test_preview_with_id(self, client, core_persona_id):
        """Test previewing personas with core persona ID."""
        response = client.get(
            "/api/personas/preview",
            params={"core_persona_id": core_persona_id, "count": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert "preview_personas" in data
        assert len(data["preview_personas"]) == 5
        
        persona = data["preview_personas"][0]
        assert "age" in persona
        assert "gender" in persona
        assert "system_prompt" in persona

    def test_preview_default_count(self, client, core_persona_id):
        """Test preview with default count."""
        response = client.get(
            "/api/personas/preview",
            params={"core_persona_id": core_persona_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["preview_personas"]) == 5

    def test_preview_without_id(self, client):
        """Test preview without ID (uses mock config)."""
        response = client.get(
            "/api/personas/preview",
            params={"count": 3}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["preview_personas"]) == 3

    def test_preview_invalid_persona(self, client):
        """Test preview with invalid persona ID."""
        response = client.get(
            "/api/personas/preview",
            params={"core_persona_id": "NONEXISTENT_ID", "count": 5}
        )
        assert response.status_code == 404

    def test_preview_system_prompt_content(self, client, core_persona_id):
        """Test that system prompts contain expected content."""
        response = client.get(
            "/api/personas/preview",
            params={"core_persona_id": core_persona_id, "count": 1}
        )
        assert response.status_code == 200
        
        prompt = response.json()["preview_personas"][0]["system_prompt"]
        assert "year-old" in prompt
        assert "consumer" in prompt
        assert "Income" in prompt
