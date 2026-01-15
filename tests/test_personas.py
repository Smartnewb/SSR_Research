"""Unit tests for persona generation module."""

from collections import Counter
import random

import pytest

from src.personas.generator import (
    Persona,
    generate_persona_template,
    generate_persona_hybrid,
    generate_personas_targeted,
    generate_personas_stratified,
    persona_to_system_prompt,
)
from src.personas.templates import TEMPLATES
from src.personas.validator import (
    validate_persona,
    validate_personas_batch,
    get_coherence_score,
)


class TestPersonaDataclass:
    """Tests for Persona dataclass."""

    def test_persona_creation(self):
        """Should create persona with required attributes."""
        persona = Persona(
            persona_id="test-001",
            age=30,
            gender="Female",
            occupation="Designer",
            location="Seoul",
            income_bracket="Medium",
            interests=["Art", "Travel"],
        )

        assert persona.persona_id == "test-001"
        assert persona.age == 30
        assert persona.gender == "Female"

    def test_persona_to_dict(self):
        """Should convert to dictionary."""
        persona = Persona(
            persona_id="test",
            age=25,
            gender="Male",
            occupation="Student",
            location="Tokyo",
            income_bracket="Low",
            interests=["Gaming"],
        )

        d = persona.to_dict()
        assert d["persona_id"] == "test"
        assert d["age"] == 25
        assert "created_at" in d


class TestGeneratePersonaTemplate:
    """Tests for template-based generation."""

    def test_generates_persona(self):
        """Should generate valid persona."""
        persona = generate_persona_template()

        assert persona.persona_id is not None
        assert 18 <= persona.age <= 80
        assert persona.gender in TEMPLATES["gender"]
        assert persona.occupation in TEMPLATES["occupation"]
        assert persona.location in TEMPLATES["location"]
        assert persona.income_bracket in TEMPLATES["income_bracket"]
        assert len(persona.interests) == 3

    def test_uses_provided_id(self):
        """Should use provided persona ID."""
        persona = generate_persona_template("custom-id")
        assert persona.persona_id == "custom-id"

    def test_deterministic_with_seed(self):
        """Should be deterministic with same seed."""
        random.seed(42)
        persona1 = generate_persona_template()

        random.seed(42)
        persona2 = generate_persona_template()

        assert persona1.age == persona2.age
        assert persona1.gender == persona2.gender
        assert persona1.occupation == persona2.occupation


class TestGeneratePersonaHybrid:
    """Tests for hybrid generation with consistency checks."""

    def test_retired_age_consistency(self):
        """Retired personas should be at least 60."""
        random.seed(0)
        for _ in range(100):
            persona = generate_persona_hybrid()
            if persona.occupation == "Retired":
                assert persona.age >= 60

    def test_student_age_consistency(self):
        """Students should not be over 30 (corrected to other occupation)."""
        random.seed(0)
        for _ in range(100):
            persona = generate_persona_hybrid()
            if persona.occupation == "Student":
                assert persona.age <= 30

    def test_high_income_occupation_consistency(self):
        """High income occupations should have high income."""
        random.seed(0)
        high_income_count = 0
        for _ in range(100):
            persona = generate_persona_hybrid()
            if persona.occupation in ["Doctor", "Lawyer"]:
                high_income_count += 1
                assert persona.income_bracket in ["High", "Very High"]

    def test_has_optional_fields(self):
        """Hybrid generation should fill optional fields."""
        persona = generate_persona_hybrid()

        assert persona.education is not None
        assert persona.tech_savviness is not None


class TestGeneratePersonasTargeted:
    """Tests for targeted persona generation."""

    def test_age_range_filter(self):
        """Should respect age range filter."""
        personas = generate_personas_targeted(
            sample_size=20,
            target_demographics={"age_range": [25, 35]},
        )

        assert len(personas) == 20
        for persona in personas:
            assert 25 <= persona.age <= 35

    def test_gender_filter(self):
        """Should respect gender filter."""
        personas = generate_personas_targeted(
            sample_size=20,
            target_demographics={"gender": ["Female"]},
        )

        assert len(personas) == 20
        for persona in personas:
            assert persona.gender == "Female"

    def test_multiple_filters(self):
        """Should respect multiple filters."""
        personas = generate_personas_targeted(
            sample_size=10,
            target_demographics={
                "age_range": [25, 40],
                "gender": ["Male", "Female"],
                "income_bracket": ["High", "Very High"],
            },
        )

        assert len(personas) == 10
        for persona in personas:
            assert 25 <= persona.age <= 40
            assert persona.gender in ["Male", "Female"]
            assert persona.income_bracket in ["High", "Very High"]

    def test_raises_on_impossible_criteria(self):
        """Should raise error if criteria too strict."""
        with pytest.raises(ValueError, match="Could not generate"):
            generate_personas_targeted(
                sample_size=100,
                target_demographics={
                    "age_range": [99, 100],
                    "occupation": ["Unicorn Tamer"],
                },
                max_attempts=100,
            )


class TestGeneratePersonasStratified:
    """Tests for stratified generation."""

    def test_generates_correct_count(self):
        """Should generate requested number of personas."""
        personas = generate_personas_stratified(100)
        assert len(personas) == 100

    def test_gender_distribution(self):
        """Should approximate gender distribution."""
        random.seed(42)
        personas = generate_personas_stratified(100)

        gender_counts = Counter(p.gender for p in personas)

        assert 40 <= gender_counts["Male"] <= 56
        assert 40 <= gender_counts["Female"] <= 56
        assert gender_counts.get("Non-binary", 0) <= 10

    def test_custom_strata(self):
        """Should respect custom strata config."""
        personas = generate_personas_stratified(
            sample_size=100,
            strata_config={
                "gender": {"Female": 1.0},
            },
        )

        female_count = sum(1 for p in personas if p.gender == "Female")
        assert female_count >= 90


class TestPersonaToSystemPrompt:
    """Tests for system prompt generation."""

    def test_includes_basic_info(self):
        """Should include basic persona info."""
        persona = Persona(
            persona_id="test",
            age=30,
            gender="Female",
            occupation="Designer",
            location="Seoul",
            income_bracket="Medium",
            interests=["Art", "Travel"],
        )

        prompt = persona_to_system_prompt(persona)

        assert "30-year-old" in prompt
        assert "female" in prompt.lower()
        assert "Designer" in prompt
        assert "Seoul" in prompt
        assert "medium income" in prompt.lower()
        assert "Art" in prompt
        assert "Travel" in prompt

    def test_includes_optional_fields(self):
        """Should include optional fields when present."""
        persona = Persona(
            persona_id="test",
            age=30,
            gender="Male",
            occupation="Engineer",
            location="Tokyo",
            income_bracket="High",
            interests=["Tech"],
            education="Master's",
            family_status="Married",
        )

        prompt = persona_to_system_prompt(persona)

        assert "Master's" in prompt
        assert "married" in prompt.lower()

    def test_no_ai_reference_instruction(self):
        """Should instruct not to break character."""
        persona = Persona(
            persona_id="test",
            age=25,
            gender="Male",
            occupation="Student",
            location="London",
            income_bracket="Low",
            interests=["Gaming"],
        )

        prompt = persona_to_system_prompt(persona)

        assert "As an AI" in prompt
        assert "break character" in prompt.lower()


class TestValidatePersona:
    """Tests for persona validation."""

    def test_valid_persona(self):
        """Should validate correct persona."""
        persona = Persona(
            persona_id="test",
            age=30,
            gender="Female",
            occupation="Designer",
            location="Seoul",
            income_bracket="Medium",
            interests=["Art", "Travel"],
        )

        is_valid, warnings = validate_persona(persona)

        assert is_valid
        assert len(warnings) == 0

    def test_invalid_age_too_young(self):
        """Should reject age below 18."""
        persona = Persona(
            persona_id="test",
            age=15,
            gender="Male",
            occupation="Student",
            location="Tokyo",
            income_bracket="Low",
            interests=["Gaming"],
        )

        is_valid, errors = validate_persona(persona)

        assert not is_valid
        assert "Age must be 18-80" in errors

    def test_invalid_age_too_old(self):
        """Should reject age above 80."""
        persona = Persona(
            persona_id="test",
            age=95,
            gender="Male",
            occupation="Retired",
            location="Tokyo",
            income_bracket="Low",
            interests=["Reading"],
        )

        is_valid, errors = validate_persona(persona)

        assert not is_valid

    def test_warning_young_retired(self):
        """Should warn about young retired person."""
        persona = Persona(
            persona_id="test",
            age=45,
            gender="Male",
            occupation="Retired",
            location="Tokyo",
            income_bracket="Medium",
            interests=["Reading"],
        )

        is_valid, warnings = validate_persona(persona)

        assert is_valid
        assert any("Retired person at age" in w for w in warnings)

    def test_warning_old_student(self):
        """Should warn about old student."""
        persona = Persona(
            persona_id="test",
            age=50,
            gender="Female",
            occupation="Student",
            location="London",
            income_bracket="Low",
            interests=["Reading"],
        )

        is_valid, warnings = validate_persona(persona)

        assert is_valid
        assert any("Student at age" in w for w in warnings)

    def test_warning_income_occupation_mismatch(self):
        """Should warn about income-occupation mismatch."""
        persona = Persona(
            persona_id="test",
            age=25,
            gender="Male",
            occupation="Student",
            location="Seoul",
            income_bracket="Very High",
            interests=["Gaming"],
        )

        is_valid, warnings = validate_persona(persona)

        assert is_valid
        assert any("income" in w.lower() for w in warnings)


class TestValidatePersonasBatch:
    """Tests for batch validation."""

    def test_separates_valid_invalid(self):
        """Should separate valid and invalid personas."""
        personas = [
            Persona(
                persona_id="valid",
                age=30,
                gender="Female",
                occupation="Designer",
                location="Seoul",
                income_bracket="Medium",
                interests=["Art"],
            ),
            Persona(
                persona_id="invalid",
                age=10,
                gender="Male",
                occupation="Student",
                location="Tokyo",
                income_bracket="Low",
                interests=["Gaming"],
            ),
        ]

        valid, invalid = validate_personas_batch(personas)

        assert len(valid) == 1
        assert len(invalid) == 1
        assert valid[0].persona_id == "valid"


class TestCoherenceScore:
    """Tests for coherence scoring."""

    def test_perfect_coherence(self):
        """Valid consistent persona should score high."""
        persona = Persona(
            persona_id="test",
            age=30,
            gender="Female",
            occupation="Designer",
            location="Seoul",
            income_bracket="Medium",
            interests=["Art"],
        )

        score = get_coherence_score(persona)
        assert score >= 0.8

    def test_low_coherence_with_warnings(self):
        """Persona with warnings should score lower."""
        persona = Persona(
            persona_id="test",
            age=25,
            gender="Male",
            occupation="Retired",
            location="Seoul",
            income_bracket="Very High",
            interests=["Gaming"],
        )

        score = get_coherence_score(persona)
        assert score < 0.7

    def test_invalid_scores_zero(self):
        """Invalid persona should score 0."""
        persona = Persona(
            persona_id="test",
            age=10,
            gender="Male",
            occupation="Student",
            location="Tokyo",
            income_bracket="Low",
            interests=["Gaming"],
        )

        score = get_coherence_score(persona)
        assert score == 0.0
