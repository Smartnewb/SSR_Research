"""Tests for multi-concept comparison functionality."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.comparison import ConceptInput


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_concepts():
    """Sample concepts for testing."""
    return [
        ConceptInput(
            id="CONCEPT_001",
            title="Colgate 3-Day White",
            headline="단 3일, 2단계 더 밝은 미소",
            consumer_insight="커피로 누렇게 변한 치아 때문에 웃기가 꺼려지시나요?",
            benefit="임상 검증된 미백 효과를 집에서 편하게",
            rtb="과산화수소 3% + 폴리싱 실리카 이중 작용",
            image_description="빨간 광택 튜브, 하얀 치아 로고",
            price="8,900원 (120g)",
        ),
        ConceptInput(
            id="CONCEPT_002",
            title="Sensodyne ProWhite",
            headline="민감하지만 하얗게",
            consumer_insight="미백 치약은 잇몸이 시려서 못 쓰셨나요?",
            benefit="민감성 완화와 미백을 동시에",
            rtb="질산칼륨 5% + 미백 실리카",
            image_description="파란색 튜브, 보호막 아이콘",
            price="12,900원 (120g)",
        ),
    ]


class TestMultiCompare:
    """Test multi-concept comparison endpoint."""

    def test_multi_compare_mock_success(self, client, sample_concepts):
        """Test multi-compare with mock mode."""
        # Save persona set
        personas = [
            {"id": f"P{i}", "age": 35, "income_bracket": "mid"} for i in range(150)
        ]
        client.post(
            "/api/surveys/multi-compare/save-persona-set",
            json={"persona_set_id": "test_set", "personas": personas},
        )

        # Run comparison
        response = client.post(
            "/api/surveys/multi-compare",
            json={
                "concepts": [c.model_dump() for c in sample_concepts],
                "persona_set_id": "test_set",
                "sample_size": 100,
                "comparison_mode": "rank_based",
                "use_mock": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "comparison_id" in data
        assert "results" in data
        assert data["personas_tested"] == 100

    def test_multi_compare_absolute_scores(self, client, sample_concepts):
        """Test absolute score calculation."""
        personas = [{"id": f"P{i}", "age": 35} for i in range(150)]
        client.post(
            "/api/surveys/multi-compare/save-persona-set",
            json={"persona_set_id": "test_abs", "personas": personas},
        )

        response = client.post(
            "/api/surveys/multi-compare",
            json={
                "concepts": [c.model_dump() for c in sample_concepts],
                "persona_set_id": "test_abs",
                "sample_size": 100,
                "comparison_mode": "absolute",
                "use_mock": True,
            },
        )

        assert response.status_code == 200
        data = response.json()

        results = data["results"]
        assert "absolute_scores" in results
        assert len(results["absolute_scores"]) == 2

        for score in results["absolute_scores"]:
            assert 0 <= score["mean_ssr"] <= 1
            assert score["std_dev"] >= 0
            assert "distribution" in score

    def test_multi_compare_validation_errors(self, client, sample_concepts):
        """Test validation errors."""
        # Test with only 1 concept (should fail, min=2)
        response = client.post(
            "/api/surveys/multi-compare",
            json={
                "concepts": [sample_concepts[0].model_dump()],
                "persona_set_id": "test",
                "sample_size": 50,
            },
        )
        assert response.status_code == 422

    def test_multi_compare_persona_set_not_found(self, client, sample_concepts):
        """Test error when persona set doesn't exist."""
        response = client.post(
            "/api/surveys/multi-compare",
            json={
                "concepts": [c.model_dump() for c in sample_concepts],
                "persona_set_id": "nonexistent",
                "sample_size": 100,
            },
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestPersonaSetManagement:
    """Test persona set save/list endpoints."""

    def test_save_persona_set(self, client):
        """Test saving a persona set."""
        personas = [{"id": f"P{i}", "age": 30 + i} for i in range(50)]

        response = client.post(
            "/api/surveys/multi-compare/save-persona-set",
            json={"persona_set_id": "my_personas", "personas": personas},
        )

        assert response.status_code == 200
        assert response.json()["persona_set_id"] == "my_personas"
        assert response.json()["count"] == 50

    def test_list_persona_sets(self, client):
        """Test listing available persona sets."""
        # Save a set first
        personas = [{"id": f"P{i}"} for i in range(25)]
        client.post(
            "/api/surveys/multi-compare/save-persona-set",
            json={"persona_set_id": "list_test", "personas": personas},
        )

        # List all sets
        response = client.get("/api/surveys/multi-compare/persona-sets")

        assert response.status_code == 200
        data = response.json()
        assert "persona_sets" in data
        assert any(s["id"] == "list_test" for s in data["persona_sets"])
