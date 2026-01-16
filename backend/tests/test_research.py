"""Tests for research API endpoints."""

import pytest


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from backend.app.main import app
    return TestClient(app)


class TestGeneratePrompt:
    """Tests for POST /api/research/generate-prompt."""

    def test_generate_prompt_mock_success(self, client):
        """Test generating research prompt with mock mode."""
        response = client.post(
            "/api/research/generate-prompt",
            params={"use_mock": True},
            json={
                "product_category": "oral care",
                "target_description": "30-40대 직장인 여성, 커피 자주 마심, 미백 관심",
                "market": "korea"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "research_prompt" in data
        assert "instructions" in data
        assert "oral care" in data["research_prompt"].lower()
        assert "Gemini" in data["instructions"]

    def test_generate_prompt_us_market(self, client):
        """Test generating prompt for US market."""
        response = client.post(
            "/api/research/generate-prompt",
            params={"use_mock": True},
            json={
                "product_category": "skincare",
                "target_description": "Young professionals interested in anti-aging",
                "market": "us"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "skincare" in data["research_prompt"].lower()

    def test_generate_prompt_invalid_market(self, client):
        """Test with invalid market value."""
        response = client.post(
            "/api/research/generate-prompt",
            params={"use_mock": True},
            json={
                "product_category": "food",
                "target_description": "Health conscious consumers",
                "market": "invalid_market"
            }
        )
        assert response.status_code == 422

    def test_generate_prompt_missing_category(self, client):
        """Test with missing product category."""
        response = client.post(
            "/api/research/generate-prompt",
            params={"use_mock": True},
            json={
                "target_description": "Young consumers",
                "market": "korea"
            }
        )
        assert response.status_code == 422


class TestParseReport:
    """Tests for POST /api/research/parse-report."""

    def test_parse_report_mock_success(self, client):
        """Test parsing research report with mock mode."""
        sample_report = """
        # Market Research Report

        ## Demographics
        Target audience is 30-40 year old professional women (연령: 30-40대).
        Gender: Primarily female (70-80%)
        
        ## Income Profile
        Average annual income: 50,000-70,000 USD
        Mid-income bracket dominant (60%)
        
        ## Category Usage
        High frequency users who purchase oral care products monthly.
        
        ## Pain Points
        - Yellow teeth from coffee consumption
        - Sensitive gums
        - High prices of premium products
        
        ## Decision Drivers
        - Proven efficacy
        - Brand reputation
        - Price-quality balance
        """
        response = client.post(
            "/api/research/parse-report",
            params={"use_mock": True},
            json={"research_report": sample_report}
        )
        assert response.status_code == 200
        data = response.json()
        assert "core_persona" in data
        assert "confidence" in data
        assert "warnings" in data
        
        persona = data["core_persona"]
        assert "age_range" in persona
        assert "gender_distribution" in persona
        assert "income_brackets" in persona
        assert "key_pain_points" in persona

    def test_parse_report_short_input(self, client):
        """Test with too short input."""
        response = client.post(
            "/api/research/parse-report",
            params={"use_mock": True},
            json={"research_report": "Too short"}
        )
        assert response.status_code == 422

    def test_parse_report_confidence_score(self, client):
        """Test that confidence score is returned."""
        sample_report = """
        # Research Report
        
        This is a detailed report about consumers aged 25-35.
        Gender distribution is 60% female, 40% male.
        Income levels are varied across low, medium, and high brackets.
        """ + " " * 100  # Padding to meet min length
        
        response = client.post(
            "/api/research/parse-report",
            params={"use_mock": True},
            json={"research_report": sample_report}
        )
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["confidence"] <= 1


class TestCorePersona:
    """Tests for /api/personas/core endpoints."""

    def test_save_core_persona_success(self, client):
        """Test saving a core persona."""
        response = client.post(
            "/api/personas/core",
            json={
                "name": "Coffee Lover Professional",
                "age_range": [30, 40],
                "gender_distribution": {"female": 60, "male": 40},
                "income_brackets": {"low": 20, "mid": 60, "high": 20},
                "location": "urban",
                "category_usage": "high",
                "shopping_behavior": "smart_shopper",
                "key_pain_points": ["yellow teeth", "sensitive gums"],
                "decision_drivers": ["efficacy", "price"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"].startswith("PERSONA_CORE_")
        assert "created_at" in data
        assert data["status"] == "ready_for_generation"

    def test_save_core_persona_invalid_gender_sum(self, client):
        """Test with gender distribution not summing to 100."""
        response = client.post(
            "/api/personas/core",
            json={
                "name": "Test Persona",
                "age_range": [25, 35],
                "gender_distribution": {"female": 60, "male": 50},  # Sum = 110
                "income_brackets": {"low": 30, "mid": 50, "high": 20},
                "location": "urban",
                "category_usage": "medium",
                "shopping_behavior": "budget",
                "key_pain_points": ["test"],
                "decision_drivers": ["test"]
            }
        )
        assert response.status_code == 422

    def test_save_core_persona_invalid_age_range(self, client):
        """Test with invalid age range."""
        response = client.post(
            "/api/personas/core",
            json={
                "name": "Test Persona",
                "age_range": [50, 30],  # min > max
                "gender_distribution": {"female": 50, "male": 50},
                "income_brackets": {"low": 30, "mid": 50, "high": 20},
                "location": "urban",
                "category_usage": "medium",
                "shopping_behavior": "budget",
                "key_pain_points": ["test"],
                "decision_drivers": ["test"]
            }
        )
        assert response.status_code == 422

    def test_get_core_persona_not_found(self, client):
        """Test getting non-existent persona."""
        response = client.get("/api/personas/core/NONEXISTENT_ID")
        assert response.status_code == 404

    def test_list_core_personas(self, client):
        """Test listing all personas."""
        # First, create a persona
        client.post(
            "/api/personas/core",
            json={
                "name": "List Test Persona",
                "age_range": [20, 30],
                "gender_distribution": {"female": 50, "male": 50},
                "income_brackets": {"low": 33, "mid": 34, "high": 33},
                "location": "suburban",
                "category_usage": "low",
                "shopping_behavior": "impulsive",
                "key_pain_points": ["test pain"],
                "decision_drivers": ["test driver"]
            }
        )
        
        response = client.get("/api/personas/core")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_saved_persona(self, client):
        """Test retrieving a saved persona."""
        # Create persona
        create_response = client.post(
            "/api/personas/core",
            json={
                "name": "Retrieval Test",
                "age_range": [25, 45],
                "gender_distribution": {"female": 70, "male": 30},
                "income_brackets": {"low": 10, "mid": 70, "high": 20},
                "location": "urban",
                "category_usage": "high",
                "shopping_behavior": "quality",
                "key_pain_points": ["point1", "point2"],
                "decision_drivers": ["driver1"]
            }
        )
        persona_id = create_response.json()["id"]
        
        # Retrieve persona
        get_response = client.get(f"/api/personas/core/{persona_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["name"] == "Retrieval Test"
        assert data["age_range"] == [25, 45]
