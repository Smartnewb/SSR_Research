"""Unit tests for SSR algorithm."""

import numpy as np
import pytest

from src.ssr.utils import (
    cosine_similarity,
    normalize_to_unit,
    to_likert_5,
    to_percentage,
    to_scale_10,
)
from src.ssr.anchors import (
    POSITIVE_ANCHOR,
    NEGATIVE_ANCHOR,
    get_anchors,
    ALTERNATIVE_ANCHORS,
)
from src.ssr.calculator import SSRCalculator


class TestCosineSimlarity:
    """Tests for cosine_similarity function."""

    def test_identical_vectors(self):
        """Identical vectors should have similarity 1.0."""
        vec = np.array([1.0, 2.0, 3.0])
        assert cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_opposite_vectors(self):
        """Opposite vectors should have similarity -1.0."""
        vec_a = np.array([1.0, 0.0, 0.0])
        vec_b = np.array([-1.0, 0.0, 0.0])
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(-1.0)

    def test_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity 0.0."""
        vec_a = np.array([1.0, 0.0, 0.0])
        vec_b = np.array([0.0, 1.0, 0.0])
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(0.0)

    def test_zero_vector(self):
        """Zero vector should return 0.0 similarity."""
        vec_a = np.array([0.0, 0.0, 0.0])
        vec_b = np.array([1.0, 2.0, 3.0])
        assert cosine_similarity(vec_a, vec_b) == 0.0

    def test_known_similarity(self):
        """Test with known similarity value."""
        vec_a = np.array([1.0, 1.0])
        vec_b = np.array([1.0, 0.0])
        # cos(45°) = √2/2 ≈ 0.707
        expected = np.sqrt(2) / 2
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(expected, rel=1e-5)


class TestNormalization:
    """Tests for normalization functions."""

    def test_normalize_to_unit(self):
        """Test normalization from [-1, 1] to [0, 1]."""
        assert normalize_to_unit(-1.0) == pytest.approx(0.0)
        assert normalize_to_unit(0.0) == pytest.approx(0.5)
        assert normalize_to_unit(1.0) == pytest.approx(1.0)

    def test_to_likert_5(self):
        """Test conversion to 1-5 Likert scale."""
        assert to_likert_5(0.0) == pytest.approx(1.0)
        assert to_likert_5(0.5) == pytest.approx(3.0)
        assert to_likert_5(1.0) == pytest.approx(5.0)

    def test_to_percentage(self):
        """Test conversion to 0-100 percentage."""
        assert to_percentage(0.0) == pytest.approx(0.0)
        assert to_percentage(0.5) == pytest.approx(50.0)
        assert to_percentage(1.0) == pytest.approx(100.0)

    def test_to_scale_10(self):
        """Test conversion to 0-10 scale."""
        assert to_scale_10(0.0) == pytest.approx(0.0)
        assert to_scale_10(0.5) == pytest.approx(5.0)
        assert to_scale_10(1.0) == pytest.approx(10.0)


class TestAnchors:
    """Tests for anchor text definitions."""

    def test_default_anchors_exist(self):
        """Default anchors should be defined."""
        assert POSITIVE_ANCHOR is not None
        assert NEGATIVE_ANCHOR is not None
        assert len(POSITIVE_ANCHOR) > 0
        assert len(NEGATIVE_ANCHOR) > 0

    def test_get_anchors_default(self):
        """get_anchors should return default anchors."""
        pos, neg = get_anchors("default")
        assert pos == POSITIVE_ANCHOR
        assert neg == NEGATIVE_ANCHOR

    def test_get_anchors_all_types(self):
        """All anchor types should be retrievable."""
        for anchor_type in ALTERNATIVE_ANCHORS:
            pos, neg = get_anchors(anchor_type)
            assert isinstance(pos, str)
            assert isinstance(neg, str)
            assert len(pos) > 0
            assert len(neg) > 0

    def test_get_anchors_invalid_type(self):
        """Invalid anchor type should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown anchor type"):
            get_anchors("invalid_type")


class TestSSRCalculator:
    """Tests for SSRCalculator class."""

    @pytest.fixture
    def mock_embedding_fn(self):
        """Mock embedding function returning normalized random vectors."""
        def embed(text: str) -> np.ndarray:
            np.random.seed(hash(text) % (2**32))
            vec = np.random.randn(1536)
            return vec / np.linalg.norm(vec)
        return embed

    @pytest.fixture
    def calculator_with_anchors(self, mock_embedding_fn):
        """Calculator with pre-initialized anchors."""
        calc = SSRCalculator(embedding_fn=mock_embedding_fn)
        calc.initialize_anchors()
        return calc

    def test_initialization_without_embedding_fn(self):
        """Should raise error when initializing without embedding function."""
        calc = SSRCalculator()
        with pytest.raises(ValueError, match="Embedding function not set"):
            calc.initialize_anchors()

    def test_calculate_without_initialization(self):
        """Should raise error when calculating before initialization."""
        calc = SSRCalculator()
        vec = np.random.randn(1536)
        with pytest.raises(ValueError, match="Anchors not initialized"):
            calc.calculate_simple(vec)

    def test_set_anchor_embeddings(self):
        """Should allow setting anchor embeddings directly."""
        calc = SSRCalculator()
        pos_vec = np.array([1.0, 0.0, 0.0])
        neg_vec = np.array([-1.0, 0.0, 0.0])

        calc.set_anchor_embeddings(pos_vec, neg_vec)

        assert calc._initialized
        assert np.array_equal(calc.pos_vec, pos_vec)
        assert np.array_equal(calc.neg_vec, neg_vec)

    def test_calculate_simple_positive_anchor(self):
        """Positive anchor should score ~1.0."""
        pos_vec = np.array([1.0, 0.0, 0.0])
        neg_vec = np.array([-1.0, 0.0, 0.0])

        calc = SSRCalculator()
        calc.set_anchor_embeddings(pos_vec, neg_vec)

        score = calc.calculate_simple(pos_vec)
        assert score == pytest.approx(1.0)

    def test_calculate_simple_negative_anchor(self):
        """Negative anchor should score ~0.0."""
        pos_vec = np.array([1.0, 0.0, 0.0])
        neg_vec = np.array([-1.0, 0.0, 0.0])

        calc = SSRCalculator()
        calc.set_anchor_embeddings(pos_vec, neg_vec)

        score = calc.calculate_simple(neg_vec)
        assert score == pytest.approx(0.0)

    def test_calculate_simple_neutral(self):
        """Neutral vector should score ~0.5."""
        pos_vec = np.array([1.0, 0.0, 0.0])
        neg_vec = np.array([-1.0, 0.0, 0.0])
        neutral_vec = np.array([0.0, 1.0, 0.0])

        calc = SSRCalculator()
        calc.set_anchor_embeddings(pos_vec, neg_vec)

        score = calc.calculate_simple(neutral_vec)
        assert score == pytest.approx(0.5)

    def test_calculate_projection_positive_anchor(self):
        """Projection method: positive anchor should score 1.0."""
        pos_vec = np.array([1.0, 0.0, 0.0])
        neg_vec = np.array([-1.0, 0.0, 0.0])

        calc = SSRCalculator()
        calc.set_anchor_embeddings(pos_vec, neg_vec)

        score = calc.calculate_projection(pos_vec)
        assert score == pytest.approx(1.0)

    def test_calculate_projection_negative_anchor(self):
        """Projection method: negative anchor should score 0.0."""
        pos_vec = np.array([1.0, 0.0, 0.0])
        neg_vec = np.array([-1.0, 0.0, 0.0])

        calc = SSRCalculator()
        calc.set_anchor_embeddings(pos_vec, neg_vec)

        score = calc.calculate_projection(neg_vec)
        assert score == pytest.approx(0.0)

    def test_calculate_projection_midpoint(self):
        """Projection method: midpoint should score 0.5."""
        pos_vec = np.array([1.0, 0.0, 0.0])
        neg_vec = np.array([-1.0, 0.0, 0.0])
        mid_vec = np.array([0.0, 0.0, 0.0])

        calc = SSRCalculator()
        calc.set_anchor_embeddings(pos_vec, neg_vec)

        score = calc.calculate_projection(mid_vec)
        assert score == pytest.approx(0.5)

    def test_calculate_batch_simple(self):
        """Batch calculation should match individual calculations."""
        pos_vec = np.array([1.0, 0.0, 0.0])
        neg_vec = np.array([-1.0, 0.0, 0.0])

        calc = SSRCalculator()
        calc.set_anchor_embeddings(pos_vec, neg_vec)

        response_vecs = np.array([
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ])

        batch_scores = calc.calculate_batch(response_vecs, method="simple")

        for i, vec in enumerate(response_vecs):
            individual_score = calc.calculate_simple(vec)
            assert batch_scores[i] == pytest.approx(individual_score, abs=1e-9)

    def test_calculate_batch_projection(self):
        """Batch projection should match individual projections."""
        pos_vec = np.array([1.0, 0.0, 0.0])
        neg_vec = np.array([-1.0, 0.0, 0.0])

        calc = SSRCalculator()
        calc.set_anchor_embeddings(pos_vec, neg_vec)

        response_vecs = np.array([
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ])

        batch_scores = calc.calculate_batch(response_vecs, method="projection")

        for i, vec in enumerate(response_vecs):
            individual_score = calc.calculate_projection(vec)
            assert batch_scores[i] == pytest.approx(individual_score)

    def test_calculate_unknown_method(self):
        """Unknown method should raise ValueError."""
        calc = SSRCalculator()
        calc.set_anchor_embeddings(np.array([1.0]), np.array([-1.0]))

        with pytest.raises(ValueError, match="Unknown method"):
            calc.calculate(np.array([0.5]), method="invalid")

    def test_scores_in_valid_range(self, calculator_with_anchors):
        """All scores should be in [0, 1] range."""
        for _ in range(100):
            vec = np.random.randn(1536)
            vec = vec / np.linalg.norm(vec)

            score_simple = calculator_with_anchors.calculate_simple(vec)
            score_proj = calculator_with_anchors.calculate_projection(vec)

            assert 0.0 <= score_simple <= 1.0
            assert 0.0 <= score_proj <= 1.0

    def test_score_variance(self, calculator_with_anchors):
        """Scores should show some variance (not all exactly equal)."""
        scores = []
        for i in range(50):
            np.random.seed(i)
            vec = np.random.randn(1536)
            vec = vec / np.linalg.norm(vec)
            scores.append(calculator_with_anchors.calculate_simple(vec))

        std_dev = np.std(scores)
        # With mock random embeddings, expect ~0.01 std dev
        # Real embeddings will have higher variance (>0.1)
        assert std_dev > 0.005, f"Scores too uniform: std={std_dev:.4f}"
        assert not all(s == scores[0] for s in scores), "All scores are identical"
