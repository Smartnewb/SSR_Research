"""Persona validation module."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .generator import Persona

from .templates import (
    TEMPLATES,
    HIGH_INCOME_OCCUPATIONS,
    LOW_INCOME_OCCUPATIONS,
)


def validate_persona(persona: "Persona") -> tuple[bool, list[str]]:
    """
    Validate persona for required fields and coherence.

    Args:
        persona: Persona to validate

    Returns:
        (is_valid, list_of_warnings)
        - is_valid: False if critical validation fails
        - warnings: List of non-blocking issues
    """
    warnings = []

    if not (18 <= persona.age <= 80):
        return False, ["Age must be 18-80"]

    if persona.gender not in TEMPLATES["gender"]:
        return False, [f"Invalid gender: {persona.gender}"]

    if not persona.interests or len(persona.interests) > 5:
        return False, ["Interests must be 1-5 items"]

    if not persona.persona_id:
        return False, ["Persona ID is required"]

    if persona.occupation == "Retired" and persona.age < 55:
        warnings.append(
            f"Retired person at age {persona.age} - unusual but possible"
        )

    if persona.occupation == "Student" and persona.age > 35:
        warnings.append(
            f"Student at age {persona.age} - unusual but possible"
        )

    if (
        persona.income_bracket in ["High", "Very High"]
        and persona.occupation in LOW_INCOME_OCCUPATIONS
    ):
        warnings.append(
            f"{persona.income_bracket} income with {persona.occupation} - check consistency"
        )

    if (
        persona.income_bracket in ["Low"]
        and persona.occupation in HIGH_INCOME_OCCUPATIONS
    ):
        warnings.append(
            f"Low income with {persona.occupation} - check consistency"
        )

    if persona.age < 22 and persona.family_status == "Married with Kids":
        warnings.append(
            f"Married with kids at age {persona.age} - unusual but possible"
        )

    return True, warnings


def validate_personas_batch(
    personas: list["Persona"],
) -> tuple[list["Persona"], list[tuple["Persona", list[str]]]]:
    """
    Validate multiple personas.

    Args:
        personas: List of personas to validate

    Returns:
        (valid_personas, invalid_personas_with_errors)
    """
    valid = []
    invalid = []

    for persona in personas:
        is_valid, errors = validate_persona(persona)
        if is_valid:
            valid.append(persona)
        else:
            invalid.append((persona, errors))

    return valid, invalid


def get_coherence_score(persona: "Persona") -> float:
    """
    Calculate coherence score for a persona (0-1).

    Higher scores indicate more realistic attribute combinations.

    Args:
        persona: Persona to score

    Returns:
        Coherence score between 0 and 1
    """
    score = 1.0
    deductions = 0.0

    is_valid, warnings = validate_persona(persona)

    if not is_valid:
        return 0.0

    deductions += len(warnings) * 0.15

    if persona.occupation == "Student" and persona.age > 30:
        deductions += 0.1
    if persona.occupation == "Retired" and persona.age < 60:
        deductions += 0.2
    if persona.occupation == "Doctor" and persona.age < 28:
        deductions += 0.1

    return max(0.0, score - deductions)
