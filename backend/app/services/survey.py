"""Survey execution service."""

import asyncio
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.pipeline import SSRPipeline
from src.ab_testing import run_ab_test, ABTestResult
from src.ssr.utils import to_likert_5, to_scale_10
from src.insights import QuickAnalyzer, QuickInsightData

from ..models.request import SurveyRequest, ABTestRequest
from ..models.response import (
    SurveyResponse,
    SurveyResultItem,
    ABTestResponse,
    ABTestStatistics,
    QuickInsight,
    PainPointPreview,
)


class SurveyService:
    """Service for running surveys and A/B tests."""

    def __init__(self, llm_model: str = "gpt-5-nano"):
        self.llm_model = llm_model
        self.pipeline = SSRPipeline(llm_model=llm_model)

    def _convert_quick_insight(self, data: QuickInsightData) -> QuickInsight:
        """Convert QuickInsightData to API response model."""
        pain_points = []
        for i, pp in enumerate(data.pain_points):
            pain_points.append(PainPointPreview(
                rank=pp.rank,
                title=pp.title,
                category=pp.category,
                is_unlocked=(i == 0),  # Only first one is unlocked
                description=pp.description if i == 0 else None,
                affected_percentage=pp.affected_percentage if i == 0 else None,
            ))

        return QuickInsight(
            one_liner=data.one_liner,
            pain_points=pain_points,
            generated_at=data.generated_at,
        )

    def run_survey(
        self,
        request: SurveyRequest,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> SurveyResponse:
        """Run a survey and return results."""
        survey_id = f"survey_{uuid.uuid4().hex[:12]}"
        start_time = time.time()

        demographics = None
        if request.demographics:
            demographics = request.demographics.model_dump(exclude_none=True)
            if demographics.get("age_range"):
                demographics["age_range"] = list(demographics["age_range"])

        if request.use_mock:
            results = self.pipeline.run_survey_mock(
                product_description=request.product_description,
                sample_size=request.sample_size,
                show_progress=False,
            )
        else:
            results = self.pipeline.run_survey(
                product_description=request.product_description,
                sample_size=request.sample_size,
                target_demographics=demographics,
                show_progress=False,
                progress_callback=progress_callback,
            )

        execution_time = time.time() - start_time

        result_items = [
            SurveyResultItem(
                persona_id=r.persona_id,
                ssr_score=r.ssr_score,
                likert_5=to_likert_5(r.ssr_score),
                scale_10=to_scale_10(r.ssr_score),
                response_text=r.response_text,
                persona_data=r.persona_data,
                tokens_used=r.tokens_used,
                cost=r.cost,
                latency_ms=r.latency_ms,
            )
            for r in results.results
        ]

        # Generate quick insight for free tier
        quick_insight = None
        if not request.use_mock and len(result_items) >= 10:
            try:
                responses_for_analysis = [
                    {
                        "persona_id": r.persona_id,
                        "response_text": r.response_text,
                        "ssr_score": r.ssr_score,
                    }
                    for r in result_items
                ]
                analyzer = QuickAnalyzer()
                insight_data = asyncio.run(
                    analyzer.analyze(responses_for_analysis, results.mean_score)
                )
                quick_insight = self._convert_quick_insight(insight_data)
            except Exception as e:
                # Log but don't fail the survey
                print(f"QuickInsight generation failed: {e}")
                quick_insight = None

        return SurveyResponse(
            survey_id=survey_id,
            product_description=request.product_description,
            sample_size=results.sample_size,
            mean_score=results.mean_score,
            median_score=results.median_score,
            std_dev=results.std_dev,
            min_score=results.min_score,
            max_score=results.max_score,
            score_distribution=results.score_distribution,
            total_cost=results.total_cost,
            total_tokens=results.total_tokens,
            execution_time_seconds=execution_time,
            results=result_items,
            quick_insight=quick_insight,
        )

    def run_ab_test(
        self,
        request: ABTestRequest,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> ABTestResponse:
        """Run an A/B test comparing two products."""
        test_id = f"abtest_{uuid.uuid4().hex[:12]}"
        start_time = time.time()

        demographics = None
        if request.demographics:
            demographics = request.demographics.model_dump(exclude_none=True)
            if demographics.get("age_range"):
                demographics["age_range"] = list(demographics["age_range"])

        ab_result = run_ab_test(
            product_a=request.product_a,
            product_b=request.product_b,
            sample_size=request.sample_size,
            product_a_name=request.product_a_name,
            product_b_name=request.product_b_name,
            llm_model=request.model,
            target_demographics=demographics,
            use_mock=request.use_mock,
            show_progress=False,
        )

        execution_time = time.time() - start_time

        def convert_results(agg_results, product_desc: str) -> SurveyResponse:
            result_items = [
                SurveyResultItem(
                    persona_id=r.persona_id,
                    ssr_score=r.ssr_score,
                    likert_5=to_likert_5(r.ssr_score),
                    scale_10=to_scale_10(r.ssr_score),
                    response_text=r.response_text,
                    persona_data=r.persona_data,
                    tokens_used=r.tokens_used,
                    cost=r.cost,
                    latency_ms=r.latency_ms,
                )
                for r in agg_results.results
            ]

            return SurveyResponse(
                survey_id=f"{test_id}_a" if "A" in product_desc else f"{test_id}_b",
                product_description=product_desc,
                sample_size=agg_results.sample_size,
                mean_score=agg_results.mean_score,
                median_score=agg_results.median_score,
                std_dev=agg_results.std_dev,
                min_score=agg_results.min_score,
                max_score=agg_results.max_score,
                score_distribution=agg_results.score_distribution,
                total_cost=agg_results.total_cost,
                total_tokens=agg_results.total_tokens,
                execution_time_seconds=execution_time / 2,
                results=result_items,
            )

        results_a = convert_results(ab_result.results_a, request.product_a)
        results_b = convert_results(ab_result.results_b, request.product_b)

        statistics = ABTestStatistics(
            mean_difference=ab_result.mean_difference,
            relative_difference=ab_result.relative_difference,
            t_statistic=ab_result.t_statistic,
            p_value=ab_result.p_value,
            confidence_interval=ab_result.confidence_interval,
            effect_size=ab_result.effect_size,
            significant=ab_result.significant,
            winner=ab_result.winner,
        )

        return ABTestResponse(
            test_id=test_id,
            product_a_name=request.product_a_name,
            product_b_name=request.product_b_name,
            results_a=results_a,
            results_b=results_b,
            statistics=statistics,
        )
