"""Gemini Deep Research integration service."""

import os
from openai import AsyncOpenAI

from ..core.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)


def _get_gemini_research_model() -> str:
    """Get model for Gemini research prompt generation."""
    return os.getenv("GEMINI_RESEARCH_MODEL", os.getenv("LLM_MODEL", "gpt-5-nano"))


async def generate_gemini_research_prompt(
    product_category: str,
    product_description: str,
    product_name: str = "",
    target_market: str = "",
    price_point: str = "",
    initial_persona_draft: dict | None = None,
) -> dict:
    """Generate a research prompt for Gemini Deep Research based on product info.

    Args:
        product_category: Category of the product
        product_description: Description of the product
        product_name: Name of the product (optional)
        target_market: Target market/country (optional)
        price_point: Price point (optional)
        initial_persona_draft: Optional initial draft of core persona (7 fields)

    Returns:
        dict with research_prompt and research_objectives
    """
    # Build product context
    product_context = f"""Product: {product_name if product_name else 'Not specified'}
Category: {product_category}
Description: {product_description}
Price Point: {price_point if price_point else 'Not specified'}
Target Market: {target_market if target_market else 'Global'}"""

    # If persona draft exists, include it as hypothesis
    persona_hypothesis = ""
    if initial_persona_draft:
        persona_hypothesis = f"""

Initial Persona Hypothesis (to validate):
Age Range: {initial_persona_draft.get('age_range', 'Unknown')}
Gender: {initial_persona_draft.get('gender_distribution', 'Unknown')}
Income: {initial_persona_draft.get('income_brackets', 'Unknown')}
Location: {initial_persona_draft.get('location', 'Unknown')}
Category Usage: {initial_persona_draft.get('category_usage', 'Unknown')}
Shopping Behavior: {initial_persona_draft.get('shopping_behavior', 'Unknown')}
Pain Points: {initial_persona_draft.get('key_pain_points', 'Unknown')}
Decision Drivers: {initial_persona_draft.get('decision_drivers', 'Unknown')}"""

    prompt = f"""You are a market research expert. Generate a comprehensive research prompt for Gemini Deep Research to identify the ideal target persona for this product.

{product_context}{persona_hypothesis}

Create a detailed research prompt (in Korean if target market is Korea/Korean, otherwise in English) that asks Gemini to:
1. Identify the ideal target consumer demographic (age, gender, income, location)
2. Analyze shopping behaviors and category usage patterns in this industry
3. Identify key pain points that this product category addresses
4. Determine primary decision drivers for purchase decisions
5. Provide market size, trends, and competitive landscape insights
6. Recommend optimal persona characteristics for this specific product

The prompt should focus on the INDUSTRY and TARGET MARKET context to build an accurate persona from scratch.

Return a JSON object with:
{{
  "research_prompt": "A detailed, actionable prompt for Gemini Deep Research (400-600 words) that focuses on market research for the {product_category} industry in {target_market if target_market else 'the target market'}",
  "research_objectives": [
    "Objective 1: Identify ideal demographic profile",
    "Objective 2: Understand category behaviors and preferences",
    "Objective 3: Map pain points and needs",
    "Objective 4: Determine decision criteria",
    "Objective 5: Analyze market and competitive context"
  ]
}}"""

    try:
        model = _get_gemini_research_model()

        # GPT-5 family (gpt-5-nano, gpt-5-mini) doesn't support temperature/reasoning_effort="none"
        # Only GPT-5.2/5.1 with reasoning_effort="none" supports temperature
        if model.startswith("gpt-5."):
            # GPT-5.2 or GPT-5.1: use reasoning_effort="none" with temperature
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a market research expert. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                reasoning_effort="none",
                temperature=0.7,
                response_format={"type": "json_object"},
            )
        else:
            # GPT-5 family (gpt-5-nano, gpt-5-mini, etc.): no temperature/reasoning_effort params
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a market research expert. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI")

        import json

        result = json.loads(content)

        return {
            "research_prompt": result.get("research_prompt", ""),
            "research_objectives": result.get("research_objectives", []),
        }

    except Exception as e:
        raise ValueError(f"Failed to generate research prompt: {e}")


async def parse_gemini_research_report(research_report: str) -> dict:
    """Parse Gemini research report and extract persona insights.

    Args:
        research_report: Text output from Gemini Deep Research

    Returns:
        dict with refined persona attributes and insights
    """
    prompt = f"""You are a market research analyst. Analyze this research report and extract structured persona data.

Research Report:
{research_report[:5000]}  # Limit to 5000 chars

Extract and return a JSON object with refined persona attributes:
{{
  "refined_demographics": {{
    "age_range": [min_age, max_age],
    "gender_distribution": {{"female": 0.XX, "male": 0.XX, "other": 0.XX}},
    "income_brackets": {{"low": 0.XX, "mid": 0.XX, "high": 0.XX}},
    "location": "urban/suburban/rural/mixed"
  }},
  "behavioral_insights": {{
    "category_usage": "high/medium/low",
    "shopping_behavior": "price_sensitive/quality_focused/brand_loyal/convenience_driven",
    "purchase_frequency": "Description of how often they buy in this category",
    "preferred_channels": ["Online", "In-store", "Mobile app", ...]
  }},
  "psychographics": {{
    "key_pain_points": ["Pain point 1", "Pain point 2", ...],
    "decision_drivers": ["Driver 1", "Driver 2", ...],
    "values": ["Value 1", "Value 2", ...],
    "lifestyle": "Description of lifestyle characteristics"
  }},
  "market_insights": {{
    "market_size": "Description of market size",
    "trends": ["Trend 1", "Trend 2", ...],
    "competitive_landscape": "Description of competition",
    "opportunities": ["Opportunity 1", "Opportunity 2", ...]
  }},
  "confidence_score": 0.XX,
  "key_findings": ["Finding 1", "Finding 2", ...]
}}

Focus on extracting actionable insights that will improve persona accuracy.
"""

    try:
        # GPT-5-nano requires Responses API (not Chat Completions)
        # Per GPT-5.2 docs: older GPT-5 models don't support temperature/top_p/logprobs
        full_prompt = f"""You are a market research analyst. Return only valid JSON.

{prompt}"""

        response = await client.responses.create(
            model="gpt-5-nano",
            input=full_prompt,
            text={"verbosity": "low"},
        )

        content = response.output_text
        if not content:
            raise ValueError("Empty response from OpenAI")

        import json
        import re

        # Extract JSON from response (may have markdown code blocks)
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if json_match:
            content = json_match.group(1)

        result = json.loads(content)
        return result

    except Exception as e:
        raise ValueError(f"Failed to parse research report: {e}")


async def generate_gemini_research_prompt_mock(
    product_category: str,
    product_description: str,
    product_name: str = "",
    target_market: str = "",
    price_point: str = "",
    initial_persona_draft: dict | None = None,
) -> dict:
    """Mock version for testing."""
    market_context = f"{target_market} " if target_market else ""

    return {
        "research_prompt": f"""다음 제품의 이상적인 타겟 페르소나를 파악하기 위한 시장 조사를 수행해주세요.

제품 정보:
- 제품명: {product_name if product_name else '미정'}
- 카테고리: {product_category}
- 설명: {product_description}
- 가격대: {price_point if price_point else '미정'}
- 타겟 시장: {target_market if target_market else '글로벌'}

다음 사항을 중점적으로 조사해주세요:

1. **인구통계학적 특성**
   - {market_context}{product_category} 제품의 주요 고객층 (연령, 성별, 소득 수준, 거주지)
   - 각 세그먼트의 시장 규모와 비중

2. **쇼핑 행동 및 카테고리 사용 패턴**
   - {product_category} 카테고리에서의 구매 빈도와 패턴
   - 온라인/오프라인 선호도
   - 정보 탐색 및 구매 결정 프로세스

3. **Pain Points (불편사항)**
   - 현재 {product_category} 제품 사용 시 겪는 주요 문제점
   - 충족되지 않는 니즈
   - 기존 솔루션의 한계

4. **구매 결정 요인**
   - {product_category} 구매 시 가장 중요하게 고려하는 요소 (가격, 품질, 브랜드, 기능 등)
   - 우선순위와 trade-off 기준

5. **시장 환경 분석**
   - {market_context}{product_category} 시장 규모와 성장률
   - 주요 경쟁사 및 시장 점유율
   - 최근 트렌드와 향후 전망

위 정보를 바탕으로 이 제품의 코어 타겟 페르소나 (연령대, 성별 분포, 소득 수준, 거주 지역, 쇼핑 성향, 주요 pain points, 구매 결정 요인)를 구체적으로 추천해주세요.""",
        "research_objectives": [
            f"{market_context}{product_category} 카테고리의 이상적인 타겟 고객 프로필 파악",
            "카테고리 내 쇼핑 행동 및 사용 패턴 이해",
            "핵심 Pain Points 및 미충족 니즈 발견",
            "구매 결정 시 주요 고려사항 및 우선순위 파악",
            "시장 규모, 트렌드, 경쟁 환경 분석",
        ],
    }


async def parse_gemini_research_report_mock(research_report: str) -> dict:
    """Mock version for testing."""
    return {
        "refined_demographics": {
            "age_range": [28, 45],
            "gender_distribution": {"female": 0.55, "male": 0.42, "other": 0.03},
            "income_brackets": {"low": 0.15, "mid": 0.60, "high": 0.25},
            "location": "urban",
        },
        "behavioral_insights": {
            "category_usage": "high",
            "shopping_behavior": "quality_focused",
            "purchase_frequency": "Monthly to quarterly purchases",
            "preferred_channels": ["Online", "Mobile app", "Specialty stores"],
        },
        "psychographics": {
            "key_pain_points": [
                "Difficulty finding reliable product information",
                "Concerns about quality vs. price trade-offs",
                "Limited time for research and comparison",
            ],
            "decision_drivers": [
                "Product quality and durability",
                "Brand reputation",
                "User reviews and ratings",
                "Value for money",
            ],
            "values": [
                "Efficiency",
                "Quality over quantity",
                "Sustainability",
                "Innovation",
            ],
            "lifestyle": "Busy professionals who value work-life balance and seek products that save time while maintaining quality",
        },
        "market_insights": {
            "market_size": "Growing market with 15-20% YoY growth in digital channels",
            "trends": [
                "Shift toward online purchasing",
                "Increased price sensitivity post-pandemic",
                "Growing preference for sustainable options",
            ],
            "competitive_landscape": "Fragmented market with mix of established brands and emerging D2C players",
            "opportunities": [
                "Underserved mid-market segment",
                "Opportunity for transparent pricing",
                "Gap in customer education content",
            ],
        },
        "confidence_score": 0.85,
        "key_findings": [
            "Target segment is older and more affluent than initially assumed",
            "Quality and brand trust are primary drivers, not just price",
            "Strong preference for online research even if purchasing offline",
            "Sustainability is becoming a key differentiator",
        ],
    }
