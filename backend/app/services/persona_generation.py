"""Enhanced persona generation service with distribution-aware sampling."""

import numpy as np
from typing import Optional


def generate_synthetic_sample(
    core_persona: dict,
    sample_size: int,
    random_seed: Optional[int] = None
) -> list[dict]:
    """
    Generate N personas following distributions from core persona.
    
    Key principle: Maintain statistical realism while introducing variation.
    Based on arXiv:2510.08338 methodology.
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    personas = []

    age_range = core_persona.get("age_range", [25, 45])
    age_mean = (age_range[0] + age_range[1]) / 2
    age_std = (age_range[1] - age_range[0]) / 6
    ages = np.random.normal(age_mean, age_std, sample_size)
    ages = np.clip(ages, age_range[0], age_range[1]).astype(int)

    gender_dist = core_persona.get("gender_distribution", {"female": 0.5, "male": 0.5})
    gender_choices = list(gender_dist.keys())
    # Values are already in 0-1 range from frontend (e.g., 0.5 for 50%)
    gender_probs = list(gender_dist.values())
    # Normalize to ensure sum is exactly 1.0
    gender_sum = sum(gender_probs)
    if gender_sum > 0:
        gender_probs = [p / gender_sum for p in gender_probs]
    genders = np.random.choice(gender_choices, sample_size, p=gender_probs)

    income_dist = core_persona.get("income_brackets", {"low": 0.3, "mid": 0.5, "high": 0.2})
    income_choices = list(income_dist.keys())
    # Values are already in 0-1 range from frontend
    income_probs = list(income_dist.values())
    # Normalize to ensure sum is exactly 1.0
    income_sum = sum(income_probs)
    if income_sum > 0:
        income_probs = [p / income_sum for p in income_probs]
    income_brackets = np.random.choice(income_choices, sample_size, p=income_probs)

    income_ranges = {
        "low": (30000, 50000),
        "mid": (50000, 100000),
        "high": (100000, 200000)
    }
    incomes = [
        np.random.randint(*income_ranges.get(bracket, (40000, 80000)))
        for bracket in income_brackets
    ]

    location = core_persona.get("location", "urban")
    category_usage = core_persona.get("category_usage", "medium")
    shopping_behavior = core_persona.get("shopping_behavior", "smart_shopper")
    pain_points = core_persona.get("key_pain_points", ["general concern"])
    decision_drivers = core_persona.get("decision_drivers", ["quality", "price"])

    for i in range(sample_size):
        persona = {
            "id": f"PERSONA_{i+1:05d}",
            "age": int(ages[i]),
            "gender": genders[i],
            "income_bracket": income_brackets[i],
            "income_value": incomes[i],
            "location": location,
            "category_usage": category_usage,
            "shopping_behavior": shopping_behavior,
            "pain_points": _vary_pain_points(pain_points, i),
            "decision_drivers": decision_drivers
        }
        personas.append(persona)

    return personas


def _vary_pain_points(core_points: list[str], seed: int) -> list[str]:
    """
    Introduce realistic variation: some personas have subset of pain points.
    80% have all pain points, 20% have random subset.
    """
    np.random.seed(seed)
    if len(core_points) <= 1 or np.random.random() < 0.8:
        return core_points
    else:
        k = np.random.randint(1, len(core_points))
        return list(np.random.choice(core_points, k, replace=False))


def persona_to_system_prompt(persona: dict) -> str:
    """
    Convert persona dict to LLM system prompt (논문 방식).
    """
    usage_text = {
        "high": "use this product daily",
        "medium": "use this product weekly",
        "low": "occasionally buy this product"
    }

    behavior_text = {
        "impulsive": "tend to make quick purchase decisions",
        "budget": "focus on getting the best value for money",
        "quality": "prioritize quality over price",
        "smart_shopper": "research thoroughly before buying"
    }

    return f"""You are a {persona['age']}-year-old {persona['gender']} consumer.

Demographics:
- Location: {persona['location']} area
- Income: ${persona['income_value']:,} per year ({persona['income_bracket']}-income bracket)

Shopping Profile:
- Category Involvement: {persona['category_usage']} (you {usage_text.get(persona['category_usage'], 'use this product regularly')})
- Shopping Behavior: {persona['shopping_behavior']} (you {behavior_text.get(persona['shopping_behavior'], 'shop thoughtfully')})

Your Key Concerns:
{chr(10).join(f'- {p}' for p in persona['pain_points'])}

What Influences Your Purchase:
{chr(10).join(f'- {d}' for d in persona['decision_drivers'])}

Respond authentically as this person would. Do not mention your age/demographics explicitly unless relevant."""


def calculate_distribution_stats(personas: list[dict]) -> dict:
    """Calculate distribution statistics for generated personas."""
    ages = [p["age"] for p in personas]
    genders = [p["gender"] for p in personas]
    incomes = [p["income_bracket"] for p in personas]

    gender_counts = {}
    for g in genders:
        gender_counts[g] = gender_counts.get(g, 0) + 1

    income_counts = {}
    for i in incomes:
        income_counts[i] = income_counts.get(i, 0) + 1

    return {
        "age": {
            "mean": float(np.mean(ages)),
            "std": float(np.std(ages)),
            "min": int(np.min(ages)),
            "max": int(np.max(ages))
        },
        "gender": gender_counts,
        "income": income_counts
    }
