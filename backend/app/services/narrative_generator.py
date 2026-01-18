"""Narrative Generator Service.

Generates readable insight reports from QIE analysis using GPT-5.2.
Uses 3 LLM calls: Executive Summary, Needs/Drivers, Segments/Actions.
"""

import asyncio
import json
import time
from typing import Optional, Callable

import openai

from ..core.config import settings
from .llm_utils import normalize_reasoning_effort


# Prompt 1: Executive Summary
EXECUTIVE_SUMMARY_PROMPT = """당신은 시장 조사 전문가입니다. 설문 분석 결과를 바탕으로 경영진/PM/마케터가 읽기 쉬운 Executive Summary를 작성하세요.

## 입력 데이터
{input_data}

## 출력 형식 (JSON)
{{
  "one_liner": "고객은 ~를 원합니다. (한 문장으로 핵심 요약)",
  "core_insights": [
    "핵심 인사이트 1 (구체적, 실행 가능)",
    "핵심 인사이트 2",
    "핵심 인사이트 3"
  ]
}}

전문 용어 없이, 비즈니스 의사결정에 도움이 되는 언어로 작성하세요."""


# Prompt 2: Needs & Drivers Analysis
NEEDS_DRIVERS_PROMPT = """당신은 시장 조사 전문가입니다. 설문 응답 데이터를 바탕으로 고객 니즈와 구매 결정 요인을 분석하세요.

## 입력 데이터
{input_data}

## 출력 형식 (JSON)
{{
  "needs_interpretation": "고객들이 무엇을 원하는지에 대한 2-3문장 해석",
  "top_needs": [
    {{
      "keyword": "키워드",
      "frequency": 50,
      "quote": "실제 응답에서 발췌한 인용문",
      "interpretation": "이 니즈가 왜 중요한지 1문장 해석"
    }}
  ],
  "drivers": [
    {{
      "factor": "촉진 요인명",
      "description": "왜 구매 의향을 높이는지",
      "quote": "관련 인용문",
      "impact_score": 85
    }}
  ],
  "barriers": [
    {{
      "factor": "저해 요인명",
      "description": "왜 구매를 망설이게 하는지",
      "quote": "관련 인용문",
      "impact_score": 70
    }}
  ]
}}

- top_needs: 상위 5개
- drivers: 상위 5개
- barriers: 상위 5개
- impact_score: 0-100 (영향력 정도)
- 모든 인용문은 실제 응답에서 가져오세요."""


# Prompt 3: Segments & Actions
SEGMENTS_ACTIONS_PROMPT = """당신은 시장 조사 전문가입니다. 분석 결과를 바탕으로 타겟 세그먼트와 실행 액션 아이템을 제안하세요.

## 입력 데이터
{input_data}

## 출력 형식 (JSON)
{{
  "segments": [
    {{
      "name": "세그먼트명 (예: 안전 최우선형)",
      "description": "이 세그먼트의 특성 1문장",
      "message": "이 세그먼트를 위한 마케팅 메시지",
      "offer": "이 세그먼트를 위한 오퍼/프로모션 제안",
      "priority_features": ["우선 기능 1", "우선 기능 2", "우선 기능 3"]
    }}
  ],
  "action_items": [
    {{
      "priority": "high",
      "title": "액션 아이템 제목",
      "description": "구체적으로 무엇을 해야 하는지",
      "category": "product"
    }}
  ]
}}

- segments: 3-5개 (가장 중요한 세그먼트)
- action_items: 5-10개
- priority: "high", "medium", "low"
- category: "product", "marketing", "operations"
- 실행 가능하고 구체적인 제안을 하세요."""


class NarrativeGenerator:
    """Generates narrative insight reports from QIE results."""

    def __init__(self, progress_callback: Optional[Callable] = None):
        self.client = openai.AsyncOpenAI()
        self.progress_callback = progress_callback

    async def _update_progress(self, stage: str, progress: float, message: str):
        if self.progress_callback:
            await self.progress_callback(stage, progress, message)

    async def generate_report(
        self,
        concept_id: str,
        concept_name: str,
        product_description: str,
        aggregated_stats: dict,
        qie_analysis: dict,
        original_responses: list[dict],
        demographics_summary: dict,
    ) -> dict:
        """Generate complete narrative report.

        Args:
            concept_id: Concept identifier
            concept_name: Human-readable concept name
            product_description: Product/concept description
            aggregated_stats: Aggregated statistics from QIE Tier 1
            qie_analysis: Analysis from QIE Tier 2
            original_responses: Original survey responses
            demographics_summary: Pre-computed demographics breakdown

        Returns:
            Complete ReportData dictionary
        """
        start_time = time.time()

        await self._update_progress(
            "report_generation", 0.0, "보고서 생성 시작..."
        )

        # Prepare sample responses for context
        sample_responses = self._prepare_sample_responses(original_responses, 20)

        # Call 1: Executive Summary
        await self._update_progress(
            "report_generation", 0.1, "Executive Summary 생성 중..."
        )
        exec_summary = await self._generate_executive_summary(
            aggregated_stats, qie_analysis, sample_responses
        )

        # Call 2: Needs & Drivers
        await self._update_progress(
            "report_generation", 0.4, "니즈/요인 분석 중..."
        )
        needs_drivers = await self._generate_needs_drivers(
            aggregated_stats, qie_analysis, sample_responses
        )

        # Call 3: Segments & Actions
        await self._update_progress(
            "report_generation", 0.7, "세그먼트/액션 생성 중..."
        )
        segments_actions = await self._generate_segments_actions(
            aggregated_stats, qie_analysis, needs_drivers
        )

        generation_time = time.time() - start_time

        await self._update_progress(
            "report_generation", 1.0, f"보고서 생성 완료 ({generation_time:.1f}초)"
        )

        # Assemble final report
        report_data = self._assemble_report(
            concept_id=concept_id,
            concept_name=concept_name,
            total_respondents=aggregated_stats.get("total_responses", 0),
            demographics_summary=demographics_summary,
            exec_summary=exec_summary,
            needs_drivers=needs_drivers,
            segments_actions=segments_actions,
            aggregated_stats=aggregated_stats,
            qie_analysis=qie_analysis,
        )

        return {
            "success": True,
            "report_data": report_data,
            "generation_time": generation_time,
        }

    def _prepare_sample_responses(
        self, responses: list[dict], limit: int
    ) -> list[dict]:
        """Prepare sample responses for LLM context."""
        # Sort by SSR score to get diverse samples
        sorted_responses = sorted(
            responses, key=lambda x: x.get("ssr_score", 0.5)
        )

        # Take from low, mid, high SSR ranges
        n = min(limit, len(sorted_responses))
        step = max(1, len(sorted_responses) // n)

        samples = []
        for i in range(0, len(sorted_responses), step):
            if len(samples) >= limit:
                break
            r = sorted_responses[i]
            samples.append({
                "text": r.get("response_text", "")[:300],
                "ssr": r.get("ssr_score", 0.5),
                "demographics": r.get("demographics", {}),
            })

        return samples

    async def _call_llm(
        self, prompt: str, input_data: dict, reasoning_effort: str = "low"
    ) -> dict:
        """Call GPT-5.2 with structured output."""
        formatted_prompt = prompt.format(
            input_data=json.dumps(input_data, ensure_ascii=False, indent=2)
        )

        for attempt in range(3):
            try:
                normalized_effort = normalize_reasoning_effort(
                    settings.qie_tier2_model,
                    reasoning_effort,
                )
                create_params = {
                    "model": settings.qie_tier2_model,
                    "input": formatted_prompt,
                    "text": {"verbosity": "medium"},
                }
                if normalized_effort:
                    create_params["reasoning"] = {"effort": normalized_effort}

                response = await self.client.responses.create(**create_params)

                output_text = response.output_text.strip()

                # Clean JSON if wrapped in markdown
                if output_text.startswith("```"):
                    output_text = output_text.split("```")[1]
                    if output_text.startswith("json"):
                        output_text = output_text[4:]
                    output_text = output_text.strip()

                return json.loads(output_text)

            except (json.JSONDecodeError, Exception) as e:
                if attempt == 2:
                    # Return empty dict on final failure
                    return {}
                await asyncio.sleep(1 * (attempt + 1))

        return {}

    async def _generate_executive_summary(
        self,
        aggregated_stats: dict,
        qie_analysis: dict,
        sample_responses: list[dict],
    ) -> dict:
        """Generate executive summary section."""
        input_data = {
            "total_responses": aggregated_stats.get("total_responses", 0),
            "avg_sentiment": aggregated_stats.get("avg_sentiment", 5),
            "keyword_frequency": dict(
                list(aggregated_stats.get("keyword_frequency", {}).items())[:10]
            ),
            "category_stats": aggregated_stats.get("category_stats", [])[:5],
            "existing_summary": qie_analysis.get("executive_summary", ""),
            "sample_responses": sample_responses[:5],
        }

        return await self._call_llm(EXECUTIVE_SUMMARY_PROMPT, input_data, "low")

    async def _generate_needs_drivers(
        self,
        aggregated_stats: dict,
        qie_analysis: dict,
        sample_responses: list[dict],
    ) -> dict:
        """Generate needs and drivers analysis."""
        input_data = {
            "keyword_frequency": aggregated_stats.get("keyword_frequency", {}),
            "category_stats": aggregated_stats.get("category_stats", []),
            "key_drivers": qie_analysis.get("key_drivers", []),
            "pain_points": qie_analysis.get("pain_points", []),
            "sample_responses": sample_responses,
        }

        return await self._call_llm(NEEDS_DRIVERS_PROMPT, input_data, "low")

    async def _generate_segments_actions(
        self,
        aggregated_stats: dict,
        qie_analysis: dict,
        needs_drivers: dict,
    ) -> dict:
        """Generate segments and action items."""
        input_data = {
            "segment_breakdown": aggregated_stats.get("segment_breakdown", {}),
            "needs_summary": needs_drivers.get("needs_interpretation", ""),
            "top_needs": needs_drivers.get("top_needs", [])[:5],
            "drivers": needs_drivers.get("drivers", [])[:3],
            "barriers": needs_drivers.get("barriers", [])[:3],
            "existing_actions": qie_analysis.get("action_items", []),
        }

        return await self._call_llm(SEGMENTS_ACTIONS_PROMPT, input_data, "medium")

    def _assemble_report(
        self,
        concept_id: str,
        concept_name: str,
        total_respondents: int,
        demographics_summary: dict,
        exec_summary: dict,
        needs_drivers: dict,
        segments_actions: dict,
        aggregated_stats: dict,
        qie_analysis: dict,
    ) -> dict:
        """Assemble all sections into final report."""
        from datetime import datetime

        # Build demographics breakdown
        segment_breakdown = aggregated_stats.get("segment_breakdown", {})

        def build_breakdown(data: dict, key: str) -> list:
            items = data.get(key, {})
            total = sum(item.get("count", 0) for item in items.values())
            result = []
            for label, item in items.items():
                count = item.get("count", 0)
                result.append({
                    "label": key.replace("by_", ""),
                    "value": label,
                    "percentage": (count / total * 100) if total > 0 else 0,
                })
            return result

        return {
            "conceptId": concept_id,
            "conceptName": concept_name,
            "generatedAt": datetime.now().isoformat(),
            "totalRespondents": total_respondents,

            "executiveSummary": {
                "oneLiner": exec_summary.get("one_liner", ""),
                "keyMetrics": {
                    "respondents": total_respondents,
                    "avgSSR": aggregated_stats.get("avg_sentiment", 5) / 10,
                    "confidenceScore": qie_analysis.get("confidence_score", 0.8),
                },
                "coreInsights": exec_summary.get("core_insights", []),
            },

            "demographics": {
                "summary": demographics_summary.get("summary", ""),
                "breakdown": {
                    "age": build_breakdown(segment_breakdown, "by_age"),
                    "gender": build_breakdown(segment_breakdown, "by_gender"),
                    "income": build_breakdown(segment_breakdown, "by_income"),
                    "location": [
                        {"label": "location", "value": "Urban", "percentage": 100}
                    ],
                },
            },

            "customerNeeds": {
                "interpretation": needs_drivers.get("needs_interpretation", ""),
                "topNeeds": [
                    {
                        "rank": i + 1,
                        "keyword": need.get("keyword", ""),
                        "frequency": need.get("frequency", 0),
                        "quote": need.get("quote", ""),
                        "interpretation": need.get("interpretation", ""),
                    }
                    for i, need in enumerate(needs_drivers.get("top_needs", [])[:5])
                ],
            },

            "driversBarriers": {
                "drivers": [
                    {
                        "rank": i + 1,
                        "factor": d.get("factor", ""),
                        "description": d.get("description", ""),
                        "quote": d.get("quote", ""),
                        "impactScore": d.get("impact_score", 50),
                    }
                    for i, d in enumerate(needs_drivers.get("drivers", [])[:5])
                ],
                "barriers": [
                    {
                        "rank": i + 1,
                        "factor": b.get("factor", ""),
                        "description": b.get("description", ""),
                        "quote": b.get("quote", ""),
                        "impactScore": b.get("impact_score", 50),
                    }
                    for i, b in enumerate(needs_drivers.get("barriers", [])[:5])
                ],
            },

            "segments": [
                {
                    "name": s.get("name", ""),
                    "description": s.get("description", ""),
                    "message": s.get("message", ""),
                    "offer": s.get("offer", ""),
                    "priorityFeatures": s.get("priority_features", []),
                }
                for s in segments_actions.get("segments", [])[:5]
            ],

            "actionItems": [
                {
                    "priority": a.get("priority", "medium"),
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "category": a.get("category", "product"),
                }
                for a in segments_actions.get("action_items", [])[:10]
            ],
        }
