"""Concept service for product concept card building."""

import json
import os
from openai import OpenAI


def _get_concept_model() -> str:
    """Get concept model from environment or fallback."""
    return os.getenv("CONCEPT_MODEL", os.getenv("LLM_MODEL", "gpt-5-nano"))


FIELD_PROMPTS = {
    "title": "Generate a catchy product name (max 50 chars). Should be memorable, unique, and suggest the product benefit.",
    "headline": "Write a one-sentence hook (10-20 words) that captures attention and communicates the key promise.",
    "insight": "Describe the consumer's pain point as a relatable question or statement that resonates emotionally.",
    "benefit": "State the core benefit/solution this product provides. Be specific and compelling.",
    "rtb": "Provide technical credibility (ingredient, technology, clinical proof, or certification).",
    "image_description": "Describe the product's appearance as if for a blind person - include colors, shapes, size, packaging.",
    "price": "Format price with context (size, promo, value comparison).",
}


async def assist_concept_field(
    field: str,
    rough_idea: str,
    context: dict
) -> list[dict]:
    """Generate 3 polished suggestions for a concept card field."""
    client = OpenAI()

    system_prompt = f"""You are a CPG (Consumer Packaged Goods) marketing copywriter with expertise in concept testing.
Write compelling product concept text following industry best practices.

Field: {field}
Task: {FIELD_PROMPTS.get(field, 'Write compelling copy for this field.')}

Target Audience: {context.get('target_persona', 'general consumers')}
Category: {context.get('product_category', 'consumer product')}

Provide 3 different versions, each with a brief rationale explaining why it works.
Output as JSON: {{"suggestions": [{{"text": "...", "rationale": "..."}}]}}"""

    response = client.chat.completions.create(
        model=_get_concept_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Rough idea: {rough_idea}\n\nGenerate 3 polished versions."}
        ],
        response_format={"type": "json_object"},
        reasoning_effort="none",
        temperature=0.8,
        max_tokens=1000,
    )

    result = json.loads(response.choices[0].message.content)
    return result.get("suggestions", [])


async def assist_concept_field_mock(
    field: str,
    rough_idea: str,
    context: dict
) -> list[dict]:
    """Mock version for testing without API calls."""
    mock_suggestions = {
        "title": [
            {"text": "WhitePro 3-Day", "rationale": "Combines benefit (white) with professional positioning"},
            {"text": "Express Bright", "rationale": "Emphasizes speed and result"},
            {"text": "ClearSmile Plus", "rationale": "Clear suggests purity, Plus suggests premium"},
        ],
        "headline": [
            {"text": "3 Days to a Brighter Smile", "rationale": "Specific timeline creates urgency and believability"},
            {"text": "Professional Whitening at Home", "rationale": "Positions as professional-grade but convenient"},
            {"text": "Smile Confidently Again", "rationale": "Emotional benefit focus"},
        ],
        "insight": [
            {"text": "Tired of hiding your smile because of coffee stains?", "rationale": "Relatable problem + emotion"},
            {"text": "Do you avoid photos because of yellow teeth?", "rationale": "Social pain point"},
            {"text": "Wish you could get dentist results without the dentist prices?", "rationale": "Value concern"},
        ],
        "benefit": [
            {"text": "Clinical-grade whitening you can do at home in just 3 days", "rationale": "Combines efficacy + convenience"},
            {"text": "Removes years of stains without damaging enamel", "rationale": "Benefit + safety assurance"},
            {"text": "Get 2 shades whiter without sensitivity", "rationale": "Specific + addresses concern"},
        ],
        "rtb": [
            {"text": "Contains 3% hydrogen peroxide, the same active ingredient dentists use", "rationale": "Professional connection"},
            {"text": "Clinically proven in 8-week study with 500 participants", "rationale": "Evidence-based"},
            {"text": "Patented enamel-shield technology prevents sensitivity", "rationale": "Technology differentiation"},
        ],
        "image_description": [
            {"text": "Sleek white tube with metallic silver cap, 'PRO' in bold blue letters, 120g size", "rationale": "Professional aesthetic"},
            {"text": "Premium black box with gold accents, tube features gradient from white to blue", "rationale": "Luxury positioning"},
            {"text": "Clean minimalist design, matte white tube with subtle sparkle effect", "rationale": "Modern, premium feel"},
        ],
        "price": [
            {"text": "$12.99 (120g) - Launch special: Buy 1 Get 1 50% Off", "rationale": "Clear value + promotion"},
            {"text": "$14.99 for 90-day supply (3 tubes)", "rationale": "Value packaging"},
            {"text": "$9.99 introductory price (regular $14.99)", "rationale": "Limited-time incentive"},
        ],
    }
    return mock_suggestions.get(field, [
        {"text": f"Sample {field} text based on: {rough_idea[:30]}...", "rationale": "Generated from user input"},
        {"text": f"Alternative {field} approach", "rationale": "Different angle"},
        {"text": f"Creative {field} option", "rationale": "Unique positioning"},
    ])


async def validate_concept(concept: dict) -> dict:
    """Validate a product concept card and provide feedback."""
    client = OpenAI()

    system_prompt = """You are a CPG concept testing expert.
Evaluate the product concept card against industry best practices.

Score each field as:
- "excellent" (best practice, compelling)
- "good" (acceptable, clear)
- "warning" (needs improvement)

Provide an overall score 0-100 and specific suggestions.

Output as JSON:
{
  "is_valid": true/false,
  "score": 0-100,
  "feedback": {
    "title": {"status": "good/warning/excellent", "message": "..."},
    ...
  },
  "suggestions": ["suggestion1", "suggestion2"]
}"""

    concept_text = "\n".join([f"{k}: {v}" for k, v in concept.items()])

    response = client.chat.completions.create(
        model=_get_concept_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Evaluate this concept:\n\n{concept_text}"}
        ],
        response_format={"type": "json_object"},
        reasoning_effort="none",
        temperature=0.3,
        max_tokens=1500,
    )

    return json.loads(response.choices[0].message.content)


async def validate_concept_mock(concept: dict) -> dict:
    """Mock version for testing without API calls."""
    feedback = {}
    total_score = 0
    suggestions = []

    checks = {
        "title": (len(concept.get("title", "")) >= 3, "Clear and memorable", "Title should be more distinctive"),
        "headline": (len(concept.get("headline", "")) >= 10, "Specific benefit with timeline", "Could be more compelling"),
        "consumer_insight": ("?" in concept.get("consumer_insight", "") or concept.get("consumer_insight", "").endswith("."), "Relatable pain point", "Make it more emotional/relatable"),
        "benefit": (len(concept.get("benefit", "")) >= 20, "Clear value proposition", "Could be more specific"),
        "rtb": (any(word in concept.get("rtb", "").lower() for word in ["clinical", "patent", "technology", "ingredient", "%"]), "Good technical credibility", "Add more specific proof points"),
        "image_description": (len(concept.get("image_description", "")) >= 30, "Adequate visual description", "Add more visual details"),
        "price": (any(char.isdigit() for char in concept.get("price", "")), "Clear pricing", "Include size or comparison"),
    }

    for field, (is_good, good_msg, warn_msg) in checks.items():
        if is_good:
            status = "good" if field != "consumer_insight" else "excellent"
            message = good_msg
            total_score += 14
        else:
            status = "warning"
            message = warn_msg
            suggestions.append(f"{field.title()}: {warn_msg}")
            total_score += 8

    return {
        "is_valid": total_score >= 60,
        "score": min(100, total_score + 2),
        "feedback": {field: {"status": checks[field][0] and "good" or "warning", "message": checks[field][1] if checks[field][0] else checks[field][2]} for field in checks},
        "suggestions": suggestions[:3] if suggestions else ["Consider A/B testing your headline variations"],
    }
