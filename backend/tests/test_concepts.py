"""Tests for concepts API endpoints."""

import pytest


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from backend.app.main import app
    return TestClient(app)


class TestConceptAssist:
    """Tests for POST /api/concepts/assist."""

    def test_assist_title_mock(self, client):
        """Test AI assistance for title field."""
        response = client.post(
            "/api/concepts/assist",
            params={"use_mock": True},
            json={
                "field": "title",
                "rough_idea": "whitening toothpaste that works in 3 days",
                "context": {
                    "product_category": "oral care",
                    "target_persona": "30-40 year old professionals"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) >= 1
        assert "text" in data["suggestions"][0]
        assert "rationale" in data["suggestions"][0]

    def test_assist_headline_mock(self, client):
        """Test AI assistance for headline field."""
        response = client.post(
            "/api/concepts/assist",
            params={"use_mock": True},
            json={
                "field": "headline",
                "rough_idea": "get whiter teeth fast",
                "context": {}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) >= 1

    def test_assist_all_fields_mock(self, client):
        """Test AI assistance for all 7 fields."""
        fields = ["title", "headline", "insight", "benefit", "rtb", "image_description", "price"]
        
        for field in fields:
            response = client.post(
                "/api/concepts/assist",
                params={"use_mock": True},
                json={
                    "field": field,
                    "rough_idea": f"sample idea for {field}",
                    "context": {}
                }
            )
            assert response.status_code == 200, f"Failed for field: {field}"
            data = response.json()
            assert "suggestions" in data

    def test_assist_invalid_field(self, client):
        """Test with invalid field name."""
        response = client.post(
            "/api/concepts/assist",
            params={"use_mock": True},
            json={
                "field": "invalid_field",
                "rough_idea": "some idea",
                "context": {}
            }
        )
        assert response.status_code == 422


class TestConceptValidate:
    """Tests for POST /api/concepts/validate."""

    def test_validate_good_concept_mock(self, client):
        """Test validation of a well-formed concept."""
        response = client.post(
            "/api/concepts/validate",
            params={"use_mock": True},
            json={
                "title": "WhitePro 3-Day",
                "headline": "Get 2 shades whiter in just 3 days",
                "consumer_insight": "Tired of hiding your smile because of coffee stains?",
                "benefit": "Clinical-grade whitening you can do at home safely",
                "rtb": "Contains 3% hydrogen peroxide, clinically proven formula",
                "image_description": "Sleek white tube with silver cap, blue accent stripe, 120g",
                "price": "$12.99 (120g) - Buy 1 Get 1 50% Off"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
        assert "score" in data
        assert "feedback" in data
        assert "suggestions" in data
        assert 0 <= data["score"] <= 100

    def test_validate_returns_feedback_for_all_fields(self, client):
        """Test that validation returns feedback for all 7 fields."""
        response = client.post(
            "/api/concepts/validate",
            params={"use_mock": True},
            json={
                "title": "Test Product",
                "headline": "A great product for everyone",
                "consumer_insight": "You have problems. This solves them.",
                "benefit": "Makes your life better in many ways",
                "rtb": "Uses advanced technology",
                "image_description": "A nice looking product",
                "price": "$10"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        expected_fields = ["title", "headline", "consumer_insight", "benefit", "rtb", "image_description", "price"]
        for field in expected_fields:
            assert field in data["feedback"], f"Missing feedback for {field}"
            assert "status" in data["feedback"][field]
            assert "message" in data["feedback"][field]

    def test_validate_minimal_concept(self, client):
        """Test validation with minimal acceptable inputs."""
        response = client.post(
            "/api/concepts/validate",
            params={"use_mock": True},
            json={
                "title": "Min Product",
                "headline": "Short headline here for validation",
                "consumer_insight": "Short insight statement for testing.",
                "benefit": "Short benefit statement here.",
                "rtb": "Short RTB statement here.",
                "image_description": "Short image description here.",
                "price": "$5.99"
            }
        )
        assert response.status_code == 200


class TestConceptSave:
    """Tests for POST /api/concepts and GET endpoints."""

    def test_save_concept_mock(self, client):
        """Test saving a concept."""
        response = client.post(
            "/api/concepts",
            params={"use_mock": True},
            json={
                "title": "SaveTest Product",
                "headline": "The best product you can buy",
                "consumer_insight": "Are you frustrated with existing options?",
                "benefit": "This product solves all your problems efficiently",
                "rtb": "Backed by 10 years of research and development",
                "image_description": "Modern white packaging with minimalist design, 200ml bottle",
                "price": "$24.99 (200ml)"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"].startswith("CONCEPT_")
        assert "validation_score" in data
        assert "created_at" in data

    def test_get_saved_concept(self, client):
        """Test retrieving a saved concept."""
        # First save a concept
        save_response = client.post(
            "/api/concepts",
            params={"use_mock": True},
            json={
                "title": "Retrieval Test",
                "headline": "Test product headline",
                "consumer_insight": "Test consumer insight here.",
                "benefit": "Test benefit statement.",
                "rtb": "Test RTB with proof.",
                "image_description": "Test image description.",
                "price": "$15.99"
            }
        )
        concept_id = save_response.json()["id"]
        
        # Then retrieve it
        get_response = client.get(f"/api/concepts/{concept_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["title"] == "Retrieval Test"
        assert data["id"] == concept_id

    def test_get_concept_not_found(self, client):
        """Test getting non-existent concept."""
        response = client.get("/api/concepts/NONEXISTENT_ID")
        assert response.status_code == 404

    def test_list_concepts(self, client):
        """Test listing all concepts."""
        # Create a concept first
        client.post(
            "/api/concepts",
            params={"use_mock": True},
            json={
                "title": "List Test",
                "headline": "For listing test",
                "consumer_insight": "Testing the list.",
                "benefit": "List benefit.",
                "rtb": "List RTB.",
                "image_description": "List image.",
                "price": "$9.99"
            }
        )
        
        response = client.get("/api/concepts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_save_concept_with_persona_id(self, client):
        """Test saving concept with associated persona."""
        response = client.post(
            "/api/concepts",
            params={"use_mock": True},
            json={
                "title": "Linked Product",
                "headline": "Product linked to persona",
                "consumer_insight": "Insight for linked product.",
                "benefit": "Benefit of linking.",
                "rtb": "RTB for linked.",
                "image_description": "Description of linked.",
                "price": "$19.99",
                "persona_id": "PERSONA_CORE_12345678"
            }
        )
        assert response.status_code == 200
        concept_id = response.json()["id"]
        
        # Verify persona_id was stored
        get_response = client.get(f"/api/concepts/{concept_id}")
        assert get_response.json()["persona_id"] == "PERSONA_CORE_12345678"
