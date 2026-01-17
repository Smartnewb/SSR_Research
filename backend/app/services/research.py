"""Research service for persona generation and concept building.

Includes Multi-Archetype Stratified Sampling pipeline (v2.0):
- Step 1: Segmentation - GPT-5.2 with high reasoning for market segmentation
- Step 2: Distribution - Pure Python/NumPy for sample allocation
- Step 3: Enrichment - GPT-5-mini with high verbosity for persona generation
"""

import json
import re
from typing import Optional

from openai import OpenAI

from ..core.config import settings


def _get_research_model() -> str:
    """Get research model from environment or fallback."""
    return settings.research_model


def _get_research_reasoning_effort() -> str:
    """Get research reasoning effort from environment or fallback."""
    return settings.research_reasoning_effort


def _get_segmentation_model() -> str:
    """Get segmentation model (highest reasoning capability)."""
    return settings.segmentation_model


def _get_segmentation_reasoning_effort() -> str:
    """Get segmentation reasoning effort (default: high for deep analysis)."""
    return settings.segmentation_reasoning_effort


SEGMENTATION_SYSTEM_PROMPT = """당신은 시장 분석 전문가입니다. 제공된 리서치 보고서를 심층 분석하여(Deep Reasoning), 이 시장의 잠재 고객을 **서로 다른 성향을 가진 3~5개 그룹(Segments)**으로 분류해 주세요.

각 그룹의 **추정 시장 점유율(share_ratio)**을 합계 1.0이 되도록 설정해야 합니다.

[분석 기준]
1. Demographics (연령대, 성별 분포)
2. Income Level (소득 수준, 가격 민감도)
3. Location (거주 지역 유형)
4. Category Usage (제품/서비스 사용 빈도)
5. Shopping Behavior (구매 성향)
6. Core Traits (핵심 특성, 동기, 가치관)

[출력 형식]
반드시 아래 JSON 스키마를 따르세요:

```json
[
  {
    "segment_name": "그룹명 (한글, 설명적)",
    "share_ratio": 0.0~1.0,
    "demographics": {
      "age_range": [min, max],
      "gender_distribution": {"female": %, "male": %}
    },
    "income_level": "none|low|mid|high",
    "location": "urban|suburban|rural|mixed",
    "category_usage": "high|medium|low",
    "shopping_behavior": "impulsive|budget|quality|smart_shopper|price_sensitive",
    "core_traits": ["특성1", "특성2", ...],
    "pain_points": ["고민1", "고민2", ...],
    "decision_drivers": ["결정요인1", "결정요인2", ...]
  }
]
```

[중요]
- share_ratio 합계는 정확히 1.0이어야 합니다
- 각 그룹은 서로 명확히 구분되는 특성을 가져야 합니다
- 실제 시장 데이터에 기반한 현실적인 비율을 추정하세요"""


async def segment_market_from_report(
    research_report: str,
    product_category: Optional[str] = None,
    target_segments: int = 4,
) -> dict:
    """
    Step 1: Segmentation - GPT-5.2 고추론 모드로 시장 세분화.

    Gemini Deep Research 보고서를 분석하여 3~5개의 핵심 타겟 그룹(Archetype)과
    점유율을 도출합니다.

    Args:
        research_report: Gemini Deep Research에서 생성된 보고서 텍스트
        product_category: 제품/서비스 카테고리 (컨텍스트 제공용)
        target_segments: 목표 세그먼트 수 (3~5, 기본값 4)

    Returns:
        dict containing:
        - archetypes: List of segmented archetypes with share_ratio
        - total_share: Should be 1.0
        - warnings: Any normalization or inference warnings
    """
    client = OpenAI(api_key=settings.openai_api_key)

    category_context = ""
    if product_category:
        category_context = f"\n[분석 대상 제품/서비스 카테고리]: {product_category}\n"

    user_prompt = f"""다음 리서치 보고서를 분석하여 {target_segments}개의 고객 세그먼트로 분류해주세요.
{category_context}
[리서치 보고서]
{research_report}

JSON 배열만 출력하세요. 마크다운 코드 블록이나 설명 없이 순수 JSON만 반환하세요."""

    full_input = f"{SEGMENTATION_SYSTEM_PROMPT}\n\n{user_prompt}"

    model = _get_segmentation_model()
    reasoning_effort = _get_segmentation_reasoning_effort()
    print(f"[segment_market] Using model: {model}, reasoning_effort: {reasoning_effort}")

    try:
        response = client.responses.create(
            model=model,
            input=full_input,
            max_output_tokens=3000,
            reasoning={"effort": reasoning_effort},
            text={"verbosity": "medium"},
        )
    except Exception as api_error:
        print(f"[segment_market] OpenAI API Error: {type(api_error).__name__}: {api_error}")
        raise

    content = response.output_text
    warnings = []

    try:
        archetypes = json.loads(content)
    except json.JSONDecodeError:
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            archetypes = json.loads(json_match.group())
        else:
            raise ValueError("Failed to parse archetypes JSON from response")

    total_share = sum(arch.get("share_ratio", 0) for arch in archetypes)

    if abs(total_share - 1.0) > 0.01:
        warnings.append(f"share_ratio 합계가 {total_share:.2f}였습니다. 1.0으로 정규화합니다.")
        for arch in archetypes:
            arch["share_ratio"] = arch.get("share_ratio", 0) / total_share

    for i, arch in enumerate(archetypes):
        if "segment_id" not in arch:
            arch["segment_id"] = f"SEGMENT_{i+1:02d}"

        gender = arch.get("demographics", {}).get("gender_distribution", {"female": 50, "male": 50})
        total_gender = gender.get("female", 50) + gender.get("male", 50)
        if total_gender != 100:
            arch["demographics"]["gender_distribution"] = {
                "female": round(gender.get("female", 50) * 100 / total_gender),
                "male": 100 - round(gender.get("female", 50) * 100 / total_gender)
            }
            warnings.append(f"{arch['segment_name']}: 성별 분포 정규화됨")

    return {
        "archetypes": archetypes,
        "total_share": 1.0,
        "segment_count": len(archetypes),
        "warnings": warnings,
    }


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
    client = OpenAI(api_key=settings.openai_api_key)

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
    client = OpenAI(api_key=settings.openai_api_key)

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
