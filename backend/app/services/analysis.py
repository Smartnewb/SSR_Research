"""Deep analysis service using GPT-5.2 for high-reasoning tasks.

This service handles:
- Survey response analysis and insight extraction
- Deal breaker identification
- Marketing strategy recommendations

Uses GPT-5.2 with high reasoning effort for complex analytical tasks.
"""

import os
from typing import Optional
from dataclasses import dataclass, field


def _get_analysis_model() -> str:
    """Get analysis model from environment or fallback."""
    return os.getenv("ANALYSIS_MODEL", "gpt-5.2")


def _get_analysis_reasoning_effort() -> str:
    """Get analysis reasoning effort from environment or fallback."""
    return os.getenv("ANALYSIS_REASONING_EFFORT", "high")


def _get_analysis_verbosity() -> str:
    """Get analysis verbosity from environment or fallback."""
    return os.getenv("ANALYSIS_VERBOSITY", "medium")


@dataclass
class AnalysisConfig:
    """Configuration for GPT-5.2 analysis."""

    model: str = field(default_factory=_get_analysis_model)
    reasoning_effort: str = field(default_factory=_get_analysis_reasoning_effort)
    verbosity: str = field(default_factory=_get_analysis_verbosity)
    max_output_tokens: int = 2000


@dataclass
class DealBreakerAnalysis:
    """Result of deal breaker analysis."""

    primary_deal_breakers: list[str]
    secondary_concerns: list[str]
    segment_specific_issues: dict[str, list[str]]
    severity_ranking: list[dict]


@dataclass
class MarketingStrategy:
    """Marketing strategy recommendations."""

    key_messages: list[str]
    target_segments: list[dict]
    positioning_recommendations: list[str]
    action_items: list[dict]


@dataclass
class SurveyAnalysisResult:
    """Complete survey analysis result."""

    executive_summary: str
    deal_breakers: DealBreakerAnalysis
    marketing_strategy: MarketingStrategy
    detailed_insights: list[str]
    confidence_score: float


async def analyze_survey_responses(
    responses: list[dict],
    product_description: str,
    ssr_statistics: dict,
    config: Optional[AnalysisConfig] = None,
) -> SurveyAnalysisResult:
    """
    Perform deep analysis of survey responses using GPT-5.2.

    Uses Responses API for improved CoT handling and cache efficiency.

    Args:
        responses: List of survey responses with persona data and response text
        product_description: The product concept being evaluated
        ssr_statistics: Aggregated SSR statistics (mean, std, distribution)
        config: Analysis configuration

    Returns:
        Comprehensive analysis with insights, deal breakers, and strategy
    """
    import openai

    config = config or AnalysisConfig()
    client = openai.OpenAI()

    analysis_prompt = _build_analysis_prompt(
        responses, product_description, ssr_statistics
    )

    full_input = f"""{ANALYSIS_SYSTEM_PROMPT}

{analysis_prompt}"""

    response = client.responses.create(
        model=config.model,
        input=full_input,
        max_output_tokens=config.max_output_tokens,
        reasoning={"effort": config.reasoning_effort},
        text={"verbosity": config.verbosity},
    )

    analysis_text = response.output_text

    return _parse_analysis_response(analysis_text)


async def extract_deal_breakers(
    negative_responses: list[dict],
    product_description: str,
    config: Optional[AnalysisConfig] = None,
) -> DealBreakerAnalysis:
    """
    Deep analysis of purchase rejection reasons.

    Uses Responses API for improved CoT handling and cache efficiency.
    Focuses on responses with low SSR scores to identify deal breakers.

    Args:
        negative_responses: Responses with SSR < 0.4
        product_description: Product concept
        config: Analysis configuration

    Returns:
        Detailed deal breaker analysis with severity ranking
    """
    import openai

    config = config or AnalysisConfig()
    client = openai.OpenAI()

    prompt = _build_deal_breaker_prompt(negative_responses, product_description)

    full_input = f"""{DEAL_BREAKER_SYSTEM_PROMPT}

{prompt}"""

    response = client.responses.create(
        model=config.model,
        input=full_input,
        max_output_tokens=config.max_output_tokens,
        reasoning={"effort": config.reasoning_effort},
        text={"verbosity": config.verbosity},
    )

    return _parse_deal_breaker_response(response.output_text)


async def generate_marketing_strategy(
    analysis_result: SurveyAnalysisResult,
    product_description: str,
    target_market: str = "korea",
    config: Optional[AnalysisConfig] = None,
) -> MarketingStrategy:
    """
    Generate marketing strategy based on survey analysis.

    Uses Responses API with high reasoning effort for actionable marketing recommendations.

    Args:
        analysis_result: Previous survey analysis
        product_description: Product concept
        target_market: Target market (korea, us, etc.)
        config: Analysis configuration

    Returns:
        Detailed marketing strategy with action items
    """
    import openai

    config = config or AnalysisConfig()
    client = openai.OpenAI()

    prompt = _build_strategy_prompt(analysis_result, product_description, target_market)

    full_input = f"""{STRATEGY_SYSTEM_PROMPT}

{prompt}"""

    response = client.responses.create(
        model=config.model,
        input=full_input,
        max_output_tokens=config.max_output_tokens,
        reasoning={"effort": config.reasoning_effort},
        text={"verbosity": config.verbosity},
    )

    return _parse_strategy_response(response.output_text)


ANALYSIS_SYSTEM_PROMPT = """You are a senior market research analyst with expertise in consumer behavior and product strategy.

Your task is to analyze survey responses from synthetic respondents evaluating a product concept.
The responses include SSR (Synthetic Survey Response) scores and qualitative feedback.

Provide deep, actionable insights that go beyond surface-level observations.
Focus on:
1. Patterns in purchase intent across demographic segments
2. Hidden concerns that may not be explicitly stated
3. Opportunities for product improvement
4. Competitive positioning implications

Output your analysis in a structured format with clear sections."""


DEAL_BREAKER_SYSTEM_PROMPT = """You are a consumer psychology expert specializing in purchase decision analysis.

Your task is to identify and analyze deal breakers - factors that cause potential customers to reject a product.

For each deal breaker:
1. Identify the root cause (not just the symptom)
2. Assess severity (critical, major, minor)
3. Determine which segments are most affected
4. Suggest potential solutions

Be specific and evidence-based. Quote relevant response text when identifying patterns."""


STRATEGY_SYSTEM_PROMPT = """You are a marketing strategist with deep experience in product launches and positioning.

Based on survey analysis and deal breaker insights, develop a comprehensive marketing strategy.

Your recommendations should be:
1. Specific and actionable (not generic advice)
2. Prioritized by impact and feasibility
3. Tailored to the identified target segments
4. Addressing the key deal breakers discovered

Include specific messaging recommendations and tactical action items."""


def _build_analysis_prompt(
    responses: list[dict],
    product_description: str,
    ssr_statistics: dict,
) -> str:
    """Build comprehensive analysis prompt."""
    response_summaries = []
    for r in responses[:50]:
        summary = f"- Persona: {r.get('persona_data', {}).get('age', 'N/A')}세, {r.get('persona_data', {}).get('gender', 'N/A')}, 소득: {r.get('persona_data', {}).get('income_bracket', 'N/A')}\n"
        summary += f"  SSR: {r.get('ssr_score', 0):.2f}\n"
        summary += f"  Response: {r.get('response_text', '')[:200]}..."
        response_summaries.append(summary)

    return f"""## Product Concept
{product_description}

## SSR Statistics
- Mean SSR: {ssr_statistics.get('mean_score', 0):.3f}
- Median SSR: {ssr_statistics.get('median_score', 0):.3f}
- Std Dev: {ssr_statistics.get('std_dev', 0):.3f}
- Sample Size: {ssr_statistics.get('sample_size', 0)}

## Score Distribution
- Definitely Buy (0.8-1.0): {ssr_statistics.get('score_distribution', {}).get('definitely_buy', 0):.1%}
- Probably Buy (0.6-0.8): {ssr_statistics.get('score_distribution', {}).get('probably_buy', 0):.1%}
- Maybe (0.4-0.6): {ssr_statistics.get('score_distribution', {}).get('maybe', 0):.1%}
- Unlikely (0.0-0.4): {ssr_statistics.get('score_distribution', {}).get('unlikely', 0):.1%}

## Sample Responses (50 of {len(responses)})
{chr(10).join(response_summaries)}

---
Analyze this data and provide:
1. Executive Summary (3-5 bullet points)
2. Key Insights by Segment
3. Primary Deal Breakers
4. Opportunities for Improvement
5. Confidence Assessment"""


def _build_deal_breaker_prompt(
    negative_responses: list[dict],
    product_description: str,
) -> str:
    """Build deal breaker analysis prompt."""
    response_details = []
    for r in negative_responses[:30]:
        detail = f"### Persona: {r.get('persona_data', {}).get('age', 'N/A')}세, {r.get('persona_data', {}).get('gender', 'N/A')}, 소득: {r.get('persona_data', {}).get('income_bracket', 'N/A')}, 소비성향: {r.get('persona_data', {}).get('shopping_behavior', 'N/A')}\n"
        detail += f"**SSR Score: {r.get('ssr_score', 0):.2f}**\n"
        detail += f"Response:\n> {r.get('response_text', '')}\n"
        response_details.append(detail)

    return f"""## Product Being Evaluated
{product_description}

## Negative Responses (SSR < 0.4)
These respondents indicated low purchase intent. Analyze their objections.

{chr(10).join(response_details)}

---
Identify:
1. **Primary Deal Breakers** (mentioned by 30%+ of negative respondents)
2. **Secondary Concerns** (mentioned by 10-30%)
3. **Segment-Specific Issues** (concerns unique to certain demographics)
4. **Severity Ranking** (which issues are most critical to address)

For each issue, provide:
- Evidence (quote relevant responses)
- Root cause analysis
- Suggested mitigation"""


def _build_strategy_prompt(
    analysis_result: SurveyAnalysisResult,
    product_description: str,
    target_market: str,
) -> str:
    """Build marketing strategy prompt."""
    deal_breakers_text = "\n".join(
        f"- {db}" for db in analysis_result.deal_breakers.primary_deal_breakers
    )
    insights_text = "\n".join(
        f"- {insight}" for insight in analysis_result.detailed_insights[:5]
    )

    market_context = {
        "korea": "한국 시장 특성을 고려하여 전략을 수립하세요. 한국어 마케팅 메시지를 포함하세요.",
        "us": "US market characteristics should be considered. Include English marketing messages.",
        "global": "Consider global market dynamics and regional variations.",
    }.get(target_market, "")

    return f"""## Product Concept
{product_description}

## Survey Analysis Summary
{analysis_result.executive_summary}

## Primary Deal Breakers to Address
{deal_breakers_text}

## Key Insights
{insights_text}

## Market Context
{market_context}

---
Develop a marketing strategy that:
1. **Key Messages**: 3-5 핵심 마케팅 메시지 (deals breakers 해소 중심)
2. **Target Segments**: 우선 타겟 세그먼트 및 접근 전략
3. **Positioning**: 경쟁 대비 포지셔닝 방향
4. **Action Items**: 구체적인 실행 과제 (우선순위 포함)"""


def _parse_analysis_response(text: str) -> SurveyAnalysisResult:
    """Parse LLM analysis response into structured result."""
    sections = text.split("##")

    executive_summary = ""
    detailed_insights = []

    for section in sections:
        if "Executive Summary" in section or "요약" in section:
            lines = section.strip().split("\n")[1:]
            executive_summary = "\n".join(lines)
        elif "Insight" in section or "인사이트" in section:
            lines = [
                line.strip("- ").strip()
                for line in section.split("\n")
                if line.strip().startswith("-")
            ]
            detailed_insights.extend(lines)

    return SurveyAnalysisResult(
        executive_summary=executive_summary or text[:500],
        deal_breakers=DealBreakerAnalysis(
            primary_deal_breakers=[],
            secondary_concerns=[],
            segment_specific_issues={},
            severity_ranking=[],
        ),
        marketing_strategy=MarketingStrategy(
            key_messages=[],
            target_segments=[],
            positioning_recommendations=[],
            action_items=[],
        ),
        detailed_insights=detailed_insights,
        confidence_score=0.8,
    )


def _parse_deal_breaker_response(text: str) -> DealBreakerAnalysis:
    """Parse deal breaker analysis response."""
    primary = []
    secondary = []
    severity = []

    lines = text.split("\n")
    current_section = None

    for line in lines:
        line = line.strip()
        if "Primary" in line or "주요" in line:
            current_section = "primary"
        elif "Secondary" in line or "부차" in line:
            current_section = "secondary"
        elif "Severity" in line or "심각" in line:
            current_section = "severity"
        elif line.startswith("-") or line.startswith("•"):
            item = line.lstrip("-•").strip()
            if current_section == "primary":
                primary.append(item)
            elif current_section == "secondary":
                secondary.append(item)

    return DealBreakerAnalysis(
        primary_deal_breakers=primary or ["Unable to extract deal breakers"],
        secondary_concerns=secondary,
        segment_specific_issues={},
        severity_ranking=severity,
    )


def _parse_strategy_response(text: str) -> MarketingStrategy:
    """Parse marketing strategy response."""
    key_messages = []
    positioning = []
    action_items = []

    lines = text.split("\n")
    current_section = None

    for line in lines:
        line = line.strip()
        if "Key Message" in line or "핵심 메시지" in line:
            current_section = "messages"
        elif "Positioning" in line or "포지셔닝" in line:
            current_section = "positioning"
        elif "Action" in line or "실행" in line:
            current_section = "actions"
        elif line.startswith("-") or line.startswith("•") or line.startswith("1."):
            item = line.lstrip("-•0123456789.").strip()
            if current_section == "messages":
                key_messages.append(item)
            elif current_section == "positioning":
                positioning.append(item)
            elif current_section == "actions":
                action_items.append({"task": item, "priority": "medium"})

    return MarketingStrategy(
        key_messages=key_messages or ["Strategy generation failed"],
        target_segments=[],
        positioning_recommendations=positioning,
        action_items=action_items,
    )
