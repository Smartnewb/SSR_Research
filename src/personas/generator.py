"""Persona generation module for synthetic respondents."""

import random
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

from .templates import (
    TEMPLATES,
    HIGH_INCOME_OCCUPATIONS,
    LOW_INCOME_OCCUPATIONS,
    DEFAULT_STRATA_CONFIG,
    AGE_RANGES,
)


@dataclass
class Persona:
    """Synthetic respondent profile."""

    persona_id: str
    age: int
    gender: str
    occupation: str
    location: str
    income_bracket: str
    interests: list[str]
    education: Optional[str] = None
    family_status: Optional[str] = None
    tech_savviness: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


def generate_persona_template(persona_id: Optional[str] = None) -> Persona:
    """
    Generate persona using random sampling from templates.

    Args:
        persona_id: Optional persona ID (generates UUID if not provided)

    Returns:
        Persona with random attributes
    """
    return Persona(
        persona_id=persona_id or str(uuid.uuid4()),
        age=random.randint(18, 80),
        gender=random.choice(TEMPLATES["gender"]),
        occupation=random.choice(TEMPLATES["occupation"]),
        location=random.choice(TEMPLATES["location"]),
        income_bracket=random.choice(TEMPLATES["income_bracket"]),
        interests=random.sample(TEMPLATES["interests"], k=3),
    )


def generate_persona_hybrid(persona_id: Optional[str] = None) -> Persona:
    """
    Generate persona with templates and rule-based consistency checks.

    Ensures realistic combinations (e.g., retired people are older,
    doctors have high income).

    Args:
        persona_id: Optional persona ID

    Returns:
        Coherent persona
    """
    persona = generate_persona_template(persona_id)

    if persona.occupation == "Retired" and persona.age < 60:
        persona.age = random.randint(60, 80)

    if persona.occupation == "Student" and persona.age > 30:
        persona.occupation = random.choice([
            "Software Engineer", "Teacher", "Designer", "Marketing Specialist"
        ])

    if persona.occupation in HIGH_INCOME_OCCUPATIONS:
        persona.income_bracket = random.choice(["High", "Very High"])
    elif persona.occupation in LOW_INCOME_OCCUPATIONS:
        persona.income_bracket = random.choice(["Low", "Medium"])

    if persona.age < 25:
        persona.family_status = random.choice(["Single", "In a Relationship"])
    elif persona.age > 60:
        persona.family_status = random.choice([
            "Married", "Married with Kids", "Divorced"
        ])

    persona.education = random.choice(TEMPLATES["education"])
    persona.tech_savviness = random.choice(TEMPLATES["tech_savviness"])

    return persona


def generate_personas_targeted(
    sample_size: int,
    target_demographics: Optional[dict] = None,
    max_attempts: int = 10000,
) -> list[Persona]:
    """
    Generate personas matching target criteria.

    Args:
        sample_size: Number of personas to generate
        target_demographics: Filters, e.g.:
            {
                "age_range": [25, 35],
                "gender": ["Female"],
                "location": ["Seoul", "Tokyo"],
                "income_bracket": ["High", "Very High"]
            }
        max_attempts: Maximum generation attempts

    Returns:
        List of matching personas

    Raises:
        ValueError: If unable to generate enough matching personas
    """
    target_demographics = target_demographics or {}
    personas = []
    attempts = 0

    while len(personas) < sample_size and attempts < max_attempts:
        attempts += 1
        persona = generate_persona_hybrid()

        if target_demographics.get("age_range"):
            min_age, max_age = target_demographics["age_range"]
            if not (min_age <= persona.age <= max_age):
                continue

        if target_demographics.get("gender"):
            if persona.gender not in target_demographics["gender"]:
                continue

        if target_demographics.get("location"):
            if persona.location not in target_demographics["location"]:
                continue

        if target_demographics.get("income_bracket"):
            if persona.income_bracket not in target_demographics["income_bracket"]:
                continue

        if target_demographics.get("occupation"):
            if persona.occupation not in target_demographics["occupation"]:
                continue

        personas.append(persona)

    if len(personas) < sample_size:
        raise ValueError(
            f"Could not generate {sample_size} personas matching criteria. "
            f"Only generated {len(personas)} after {max_attempts} attempts. "
            "Consider relaxing the target demographics."
        )

    return personas


def generate_personas_stratified(
    sample_size: int,
    strata_config: Optional[dict] = None,
) -> list[Persona]:
    """
    Generate personas with guaranteed demographic diversity.

    Args:
        sample_size: Total number of personas
        strata_config: Stratification rules, e.g.:
            {
                "gender": {"Male": 0.48, "Female": 0.48, "Non-binary": 0.04},
                "age_group": {
                    "18-25": 0.15,
                    "26-35": 0.25,
                    ...
                }
            }

    Returns:
        List of personas matching distributions
    """
    strata_config = strata_config or DEFAULT_STRATA_CONFIG
    personas = []

    gender_distribution = strata_config.get("gender", {})
    for gender, proportion in gender_distribution.items():
        count = int(sample_size * proportion)
        for _ in range(count):
            persona = generate_persona_hybrid()
            persona.gender = gender
            personas.append(persona)

    age_distribution = strata_config.get("age_group", {})
    for i, (age_group, proportion) in enumerate(age_distribution.items()):
        count = int(sample_size * proportion)
        start_idx = i * count
        end_idx = min(start_idx + count, len(personas))

        for j in range(start_idx, end_idx):
            if j < len(personas) and age_group in AGE_RANGES:
                min_age, max_age = AGE_RANGES[age_group]
                personas[j].age = random.randint(min_age, max_age)

                if personas[j].age >= 60:
                    personas[j].occupation = random.choice([
                        "Retired", "Manager", "Doctor", "Lawyer", "Entrepreneur"
                    ])
                elif personas[j].age <= 25 and personas[j].occupation == "Retired":
                    personas[j].occupation = random.choice([
                        "Student", "Software Engineer", "Retail Worker"
                    ])

    while len(personas) < sample_size:
        personas.append(generate_persona_hybrid())

    return personas[:sample_size]


def persona_to_system_prompt(persona: Persona) -> str:
    """
    Generate system prompt that enforces persona identity.

    The LLM will respond as if it IS this person.

    Args:
        persona: Persona to convert

    Returns:
        System prompt string
    """
    prompt = f"""You are a {persona.age}-year-old {persona.gender.lower()} who works as a {persona.occupation}.
You live in {persona.location} and have a {persona.income_bracket.lower()} income.
Your main interests are: {", ".join(persona.interests)}."""

    if persona.education:
        prompt += f"\nYour education level is {persona.education}."

    if persona.family_status:
        prompt += f"\nYou are {persona.family_status.lower()}."

    prompt += """

When responding to product concepts, answer as yourself - consider your lifestyle,
budget, needs, and preferences. Be authentic and specific to your situation.
Do NOT say "As an AI" or break character. You are a real person."""

    return prompt
