"""Research service for persona generation and concept building."""

import json
import os
import re
from typing import Optional

from openai import OpenAI


def _get_research_model() -> str:
    """Get research model from environment or fallback."""
    return os.getenv("RESEARCH_MODEL", "gpt-5.2")


def _get_research_reasoning_effort() -> str:
    """Get research reasoning effort from environment or fallback."""
    return os.getenv("RESEARCH_REASONING_EFFORT", "medium")


RESEARCH_PROMPT_SYSTEM = """You are a market research expert specializing in consumer insights.
Generate detailed research prompts for AI deep research tools (like Gemini Deep Research).

Focus on these 6 critical dimensions (based on arXiv:2510.08338):
1. Demographics (age, gender, location)
2. Income/Education (affects price sensitivity)
3. Category Usage (frequency of product usage - MOST IMPORTANT)
4. Shopping Behavior (impulsive, budget-conscious, quality-focused)
5. Pain Points (problems they want solved)
6. Decision Drivers (what influences purchase)

Output the research prompt in English for best results with Gemini.
Make it comprehensive and structured."""


PARSE_REPORT_SYSTEM = """You are a data extraction expert.
Parse market research reports and extract structured persona attributes.

Required outputs (MUST be valid JSON):
{
  "age_range": [min, max],  // integers
  "gender_distribution": {"female": %, "male": %},  // must sum to 100
  "income_brackets": {"low": %, "mid": %, "high": %},  // must sum to 100
  "location": "urban" | "suburban" | "rural" | "mixed",
  "category_usage": "high" | "medium" | "low",
  "shopping_behavior": "impulsive" | "budget" | "quality" | "smart_shopper",
  "key_pain_points": ["point1", "point2", ...],  // 2-5 strings
  "decision_drivers": ["driver1", "driver2", ...]  // 2-5 strings
}

If data is missing:
- Make reasonable inferences from context
- Note missing fields in a separate "warnings" array
- Always provide complete output

Output ONLY valid JSON, no markdown or explanations."""


async def generate_research_prompt(
    product_category: str,
    target_description: str,
    market: str = "korea"
) -> dict:
    """Generate a comprehensive research prompt for Gemini Deep Research.

    Uses Responses API for improved CoT handling and cache efficiency.
    """
    client = OpenAI()

    market_context = {
        "korea": "Korean market, provide Korean consumer insights",
        "us": "United States market, American consumer behavior",
        "global": "Global market perspective",
        "japan": "Japanese market, local consumer preferences",
        "china": "Chinese market, local e-commerce trends",
        "europe": "European market, regional variations",
    }

    user_prompt = f"""Generate a research prompt for:
- Product Category: {product_category}
- Target Audience: {target_description}
- Market: {market} ({market_context.get(market, 'global perspective')})

Create a detailed prompt that will help gather:
1. Demographic profile of the target
2. Income distribution and price sensitivity
3. Product category usage frequency
4. Shopping behavior patterns
5. Key pain points and frustrations
6. Purchase decision drivers

Make the prompt comprehensive enough to gather quantitative data where possible."""

    full_input = f"""{RESEARCH_PROMPT_SYSTEM}

{user_prompt}"""

    response = client.responses.create(
        model=_get_research_model(),
        input=full_input,
        max_output_tokens=1500,
        reasoning={"effort": _get_research_reasoning_effort()},
        text={"verbosity": "medium"},
    )

    research_prompt = response.output_text

    instructions = {
        "korea": "복사해서 Gemini Deep Research에 붙여넣으세요. 약 10분 후 보고서를 다시 이 페이지에 붙여넣으세요.",
        "us": "Copy and paste into Gemini Deep Research. Paste the report back here after ~10 minutes.",
        "global": "Copy and paste into Gemini Deep Research. Paste the report back here after ~10 minutes.",
    }.get(market, "Copy and paste into Gemini Deep Research. Paste the report back here after ~10 minutes.")

    return {
        "research_prompt": research_prompt,
        "instructions": instructions,
    }


async def parse_research_report(research_report: str) -> dict:
    """Parse a Gemini research report and extract structured persona data.

    Uses Responses API for improved CoT handling and cache efficiency.
    """
    client = OpenAI()

    full_input = f"""{PARSE_REPORT_SYSTEM}

Parse this research report:

{research_report}"""

    response = client.responses.create(
        model=_get_research_model(),
        input=full_input,
        max_output_tokens=2000,
        reasoning={"effort": "low"},
        text={"verbosity": "low", "format": {"type": "json_object"}},
    )

    content = response.output_text

    try:
        extracted = json.loads(content)
    except json.JSONDecodeError:
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            extracted = json.loads(json_match.group())
        else:
            raise ValueError("Failed to parse JSON from response")

    warnings = extracted.pop("warnings", [])

    gender = extracted.get("gender_distribution", {"female": 50, "male": 50})
    if gender.get("female", 50) + gender.get("male", 50) != 100:
        total = gender.get("female", 50) + gender.get("male", 50)
        gender["female"] = round(gender.get("female", 50) * 100 / total)
        gender["male"] = 100 - gender["female"]
        warnings.append("Gender distribution normalized to sum to 100")

    income = extracted.get("income_brackets", {"low": 30, "mid": 50, "high": 20})
    total_income = income.get("low", 30) + income.get("mid", 50) + income.get("high", 20)
    if total_income != 100:
        income["low"] = round(income.get("low", 30) * 100 / total_income)
        income["mid"] = round(income.get("mid", 50) * 100 / total_income)
        income["high"] = 100 - income["low"] - income["mid"]
        warnings.append("Income brackets normalized to sum to 100")

    confidence = 0.85
    required_fields = ["age_range", "gender_distribution", "income_brackets",
                       "category_usage", "key_pain_points", "decision_drivers"]
    missing = [f for f in required_fields if f not in extracted or not extracted[f]]
    confidence -= len(missing) * 0.1

    return {
        "core_persona": {
            "age_range": extracted.get("age_range", [25, 45]),
            "gender_distribution": gender,
            "income_brackets": income,
            "location": extracted.get("location", "urban"),
            "category_usage": extracted.get("category_usage", "medium"),
            "shopping_behavior": extracted.get("shopping_behavior", "smart_shopper"),
            "key_pain_points": extracted.get("key_pain_points", ["general concerns"]),
            "decision_drivers": extracted.get("decision_drivers", ["quality", "price"]),
        },
        "confidence": max(0.5, confidence),
        "warnings": warnings,
    }


async def generate_research_prompt_mock(
    product_category: str,
    target_description: str,
    market: str = "korea"
) -> dict:
    """Mock version for testing without API calls."""
    return {
        "research_prompt": f"""Analyze {market.title()} consumers interested in {product_category}:

Target Profile: {target_description}

Research Focus Areas:
1. Demographics: Age distribution, gender split, urban/suburban/rural location
2. Income Profile: Salary ranges, spending capacity on {product_category}
3. Category Usage: Purchase frequency, brand loyalty, usage occasions
4. Shopping Behavior: Price sensitivity, quality focus, impulse vs. planned purchases
5. Pain Points: Top 3-5 frustrations with current {product_category} products
6. Decision Drivers: Key factors influencing purchase decisions

Provide quantitative data (percentages, averages) where available.
Include qualitative insights from consumer research.""",
        "instructions": "복사해서 Gemini Deep Research에 붙여넣으세요. 약 10분 후 보고서를 다시 이 페이지에 붙여넣으세요." if market == "korea" else "Copy and paste into Gemini Deep Research. Paste the report back here after ~10 minutes.",
    }


async def parse_research_report_mock(research_report: str) -> dict:
    """Mock version for testing without API calls."""
    has_age = any(word in research_report.lower() for word in ["age", "나이", "연령"])
    has_gender = any(word in research_report.lower() for word in ["gender", "female", "male", "여성", "남성"])
    has_income = any(word in research_report.lower() for word in ["income", "salary", "소득", "연봉"])

    warnings = []
    if not has_age:
        warnings.append("Age data not found, using default range")
    if not has_gender:
        warnings.append("Gender distribution not found, using 50/50 default")
    if not has_income:
        warnings.append("Income data not found, using default distribution")

    return {
        "core_persona": {
            "age_range": [30, 40],
            "gender_distribution": {"female": 60, "male": 40},
            "income_brackets": {"low": 20, "mid": 60, "high": 20},
            "location": "urban",
            "category_usage": "high",
            "shopping_behavior": "smart_shopper",
            "key_pain_points": [
                "High price of premium products",
                "Lack of visible results",
                "Inconvenient application process"
            ],
            "decision_drivers": [
                "Proven efficacy",
                "Reasonable price",
                "Positive reviews"
            ],
        },
        "confidence": 0.75 if warnings else 0.90,
        "warnings": warnings,
    }
