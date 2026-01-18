"""Quick insight analyzer for free tier survey results."""

import asyncio
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import openai

from .tier1_tagger import Tier1Tagger, Tier1TagResult
from ..llm_utils import get_max_tokens_param, normalize_reasoning_effort


QUICK_SUMMARY_PROMPT = """You are a market research analyst. Based on the aggregated survey data below,
provide a BRIEF insight for a free preview.

## Survey Statistics
- Total responses: {total}
- Average SSR score: {mean:.2f} (0-1 scale, 1=high purchase intent)
- Category distribution: {category_dist}
- Top keywords in low-SSR responses (SSR < 0.4): {low_ssr_keywords}
- Top keywords in high-SSR responses (SSR > 0.7): {high_ssr_keywords}

## Your Task
Generate JSON with:
1. one_liner: 1-2 sentence summary of key finding (in Korean, max 150 chars)
2. pain_points: Top 3 purchase barriers, each with:
   - title: Short title (Korean, max 20 chars)
   - category: Price/UX/Trust/Feature/Convenience
   - description: 2-3 sentences explaining the issue (Korean)
   - affected_percentage: estimated % of responses mentioning this issue

Output ONLY valid JSON:
{{
  "one_liner": "...",
  "pain_points": [
    {{"title": "...", "category": "...", "description": "...", "affected_percentage": 45.2}},
    {{"title": "...", "category": "...", "description": "...", "affected_percentage": 30.1}},
    {{"title": "...", "category": "...", "description": "...", "affected_percentage": 15.5}}
  ]
}}

IMPORTANT:
- Be concise - this is a FREE preview, not full analysis
- Focus on problems, not solutions (solutions are in paid tier)
- Korean language for all text fields
- Return exactly 3 pain_points sorted by affected_percentage descending"""


@dataclass
class PainPointData:
    """Pain point data from analysis."""

    rank: int
    title: str
    category: str
    description: str
    affected_percentage: float


@dataclass
class QuickInsightData:
    """Quick insight analysis result."""

    one_liner: str
    pain_points: list[PainPointData]
    generated_at: datetime


class QuickAnalyzer:
    """Analyzer for generating free-tier quick insights."""

    def __init__(
        self,
        tier1_model: str = "gpt-5-mini",
        summary_model: str = "gpt-5-mini",
        max_concurrent: int = 20,
    ):
        self.tagger = Tier1Tagger(model=tier1_model, max_concurrent=max_concurrent)
        self.summary_model = summary_model
        self.client = openai.AsyncOpenAI()

    async def analyze(
        self,
        responses: list[dict],
        mean_score: float,
    ) -> QuickInsightData:
        """Generate quick insights from survey responses.

        Args:
            responses: List of dicts with persona_id, response_text, ssr_score
            mean_score: Mean SSR score of the survey

        Returns:
            QuickInsightData with one_liner and pain_points
        """
        # Step 1: Tag all responses
        tagged_results = await self.tagger.tag_batch(responses)

        # Step 2: Aggregate statistics
        stats = self._aggregate_stats(tagged_results)

        # Step 3: Generate summary
        insight = await self._generate_summary(stats, mean_score, len(responses))

        return insight

    def _aggregate_stats(
        self,
        results: list[Tier1TagResult],
    ) -> dict:
        """Aggregate Tier1 results into statistics."""
        category_counts: Counter = Counter()
        low_ssr_keywords: Counter = Counter()
        high_ssr_keywords: Counter = Counter()

        for r in results:
            category_counts[r.category] += 1

            if r.ssr_score < 0.4:
                low_ssr_keywords.update(r.keywords)
            elif r.ssr_score > 0.7:
                high_ssr_keywords.update(r.keywords)

        total = len(results)
        category_dist = {
            cat: f"{count} ({count/total*100:.1f}%)"
            for cat, count in category_counts.most_common()
        }

        return {
            "category_dist": category_dist,
            "low_ssr_keywords": [kw for kw, _ in low_ssr_keywords.most_common(10)],
            "high_ssr_keywords": [kw for kw, _ in high_ssr_keywords.most_common(10)],
        }

    async def _generate_summary(
        self,
        stats: dict,
        mean_score: float,
        total: int,
    ) -> QuickInsightData:
        """Generate one-liner and pain points using LLM."""
        prompt = QUICK_SUMMARY_PROMPT.format(
            total=total,
            mean=mean_score,
            category_dist=stats["category_dist"],
            low_ssr_keywords=", ".join(stats["low_ssr_keywords"][:10]) or "없음",
            high_ssr_keywords=", ".join(stats["high_ssr_keywords"][:10]) or "없음",
        )

        try:
            reasoning_effort = normalize_reasoning_effort(self.summary_model, "minimal")
            create_params = {
                "model": self.summary_model,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
                **get_max_tokens_param(self.summary_model, 800),
            }
            if reasoning_effort:
                create_params["reasoning_effort"] = reasoning_effort

            completion = await self.client.chat.completions.create(**create_params)

            content = completion.choices[0].message.content or "{}"
            # Remove markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            data = json.loads(content)

            pain_points = []
            for i, pp in enumerate(data.get("pain_points", [])[:3], start=1):
                pain_points.append(PainPointData(
                    rank=i,
                    title=pp.get("title", f"문제점 {i}")[:50],
                    category=pp.get("category", "Other"),
                    description=pp.get("description", ""),
                    affected_percentage=float(pp.get("affected_percentage", 0)),
                ))

            return QuickInsightData(
                one_liner=data.get("one_liner", "분석 결과를 확인하세요.")[:200],
                pain_points=pain_points,
                generated_at=datetime.now(),
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback
            return QuickInsightData(
                one_liner="설문 분석이 완료되었습니다. 상세 내용은 AI 심층 분석을 이용해주세요.",
                pain_points=[
                    PainPointData(
                        rank=1,
                        title="분석 필요",
                        category="Other",
                        description="AI 심층 분석을 통해 상세한 인사이트를 확인하세요.",
                        affected_percentage=0,
                    )
                ],
                generated_at=datetime.now(),
            )
