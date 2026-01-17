"""QIE (Qualitative Insight Engine) Pipeline.

Two-Tier Map-Reduce Strategy:
- Tier 1 (Map): gpt-5-mini for data structuring (parallel batch processing)
- Tier 2 (Reduce): gpt-5.2 for insight synthesis (deep reasoning)
"""

import asyncio
import json
import time
from collections import Counter
from dataclasses import asdict
from typing import Callable, Optional

import openai

from ..core.config import settings
from ..models.qie import (
    ActionItem,
    ActionPriority,
    AggregatedStats,
    CategoryStats,
    ImpactDirection,
    KanoCategory,
    KanoClassification,
    KanoFeature,
    KeyDriver,
    PainPoint,
    QIEAnalysis,
    QIEJob,
    QIEJobStatus,
    SegmentAnalysis,
    SegmentInsight,
    SentimentCategory,
    Tier1Result,
)

# Tier 1 System Prompt - Data Labeling (gpt-5-mini)
TIER1_SYSTEM_PROMPT = """You are a precise data labeler for market research analysis.

For the given survey response, extract:
1. sentiment: Integer 1-10 (1=very negative, 10=very positive purchase intent)
2. category: ONE of [Price, UX, Trust, Feature, Convenience, Other]
3. keywords: Maximum 5 key words/phrases from the response

Output ONLY valid JSON, no explanation:
{"sentiment": 7, "category": "Price", "keywords": ["affordable", "value"]}"""

# Tier 2 System Prompt - Insight Synthesis (gpt-5.2)
TIER2_SYSTEM_PROMPT = """You are a Senior Market Research Analyst with expertise in consumer behavior analysis.

Your task is to synthesize aggregated survey data into actionable insights using established frameworks.

## Analysis Frameworks to Apply:

### 1. Key Driver Analysis (KDA)
Identify factors that most strongly correlate with purchase intent (SSR score).
- Positive drivers: Keywords/categories associated with high SSR (>0.7)
- Negative drivers (barriers): Keywords/categories associated with low SSR (<0.4)

### 2. Kano Model Classification
Classify identified features/attributes into:
- Must-be: Basic expectations (absence causes dissatisfaction)
- Performance: Linear satisfaction (more is better)
- Delighter: Unexpected features that create excitement
- Indifferent: No impact on satisfaction

### 3. Sentiment Stratification
Analyze sentiment patterns across demographic segments:
- Age groups (20s, 30s, 40s, 50+)
- Gender differences
- Income level variations

## Output Format (Markdown):

### Executive Summary
[3-5 bullet points summarizing key findings]

### Key Drivers
[List positive and negative drivers with evidence]

### Kano Classification
[Feature categorization with reasoning]

### Segment Analysis
[Demographic-specific insights]

### Pain Points
[Critical issues to address, scored by severity 0-100]

### Action Items
[Prioritized recommendations: immediate/high/medium/low]

Be specific, evidence-based, and actionable. Reference actual data from the statistics provided."""


class QIEPipeline:
    """Two-Tier QIE Pipeline for qualitative insight generation."""

    def __init__(self, progress_callback: Optional[Callable] = None):
        """Initialize pipeline with optional progress callback.

        Args:
            progress_callback: Async function(stage, progress, message) for status updates
        """
        self.client = openai.AsyncOpenAI()
        self.progress_callback = progress_callback
        self.tier1_semaphore = asyncio.Semaphore(settings.qie_tier1_batch_size)

    async def _update_progress(self, stage: str, progress: float, message: str):
        """Send progress update if callback is set."""
        if self.progress_callback:
            await self.progress_callback(stage, progress, message)

    async def run_full_analysis(
        self,
        responses: list[dict],
        product_description: str,
    ) -> tuple[list[Tier1Result], AggregatedStats, QIEAnalysis, dict]:
        """Run complete QIE analysis pipeline.

        Args:
            responses: List of survey responses with ssr_score, response_text, demographics
            product_description: Product concept being evaluated

        Returns:
            Tuple of (tier1_results, aggregated_stats, analysis, timing_info)
        """
        total_start = time.time()

        # Tier 1: Data Structuring
        await self._update_progress(
            "tier1_processing", 0.0, f"응답 태깅 시작 (총 {len(responses)}건)..."
        )
        tier1_start = time.time()
        tier1_results = await self.run_tier1_batch(responses)
        tier1_time = time.time() - tier1_start

        # Aggregation
        await self._update_progress(
            "aggregating", 0.6, "통계 집계 중..."
        )
        aggregated_stats = self.aggregate_tier1_results(tier1_results, responses)

        # Tier 2: Insight Synthesis
        await self._update_progress(
            "tier2_synthesis", 0.7, "심층 분석 중 (GPT-5.2 추론)..."
        )
        tier2_start = time.time()
        analysis = await self.run_tier2_synthesis(
            aggregated_stats, product_description, responses
        )
        tier2_time = time.time() - tier2_start

        total_time = time.time() - total_start

        await self._update_progress(
            "completed", 1.0, f"분석 완료 (총 {total_time:.1f}초)"
        )

        timing_info = {
            "total_time": total_time,
            "tier1_time": tier1_time,
            "tier2_time": tier2_time,
        }

        return tier1_results, aggregated_stats, analysis, timing_info

    async def run_tier1_batch(
        self, responses: list[dict]
    ) -> list[Tier1Result]:
        """Process responses with gpt-5-mini in parallel batches.

        Uses semaphore to limit concurrent requests (rate limit aware).
        """
        async def process_single(response: dict, index: int) -> Tier1Result:
            async with self.tier1_semaphore:
                result = await self._tier1_process_response(response)

                # Progress update every 10 responses
                if (index + 1) % 10 == 0:
                    progress = 0.5 * (index + 1) / len(responses)
                    await self._update_progress(
                        "tier1_processing",
                        progress,
                        f"응답 태깅 중... ({index + 1}/{len(responses)})"
                    )

                return result

        tasks = [
            process_single(response, i)
            for i, response in enumerate(responses)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed results
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create fallback result for failed processing
                valid_results.append(
                    Tier1Result(
                        response_id=responses[i].get("persona_id", f"resp_{i}"),
                        sentiment=5,
                        category=SentimentCategory.OTHER,
                        keywords=[],
                        original_text=responses[i].get("response_text", "")[:200],
                        ssr_score=responses[i].get("ssr_score", 0.5),
                    )
                )
            else:
                valid_results.append(result)

        return valid_results

    async def _tier1_process_response(self, response: dict) -> Tier1Result:
        """Process a single response with gpt-5-mini."""
        response_text = response.get("response_text", "")
        ssr_score = response.get("ssr_score", 0.5)
        persona_id = response.get("persona_id", "unknown")

        user_prompt = f"""Survey Response:
"{response_text}"

SSR Score: {ssr_score:.2f}

Extract sentiment, category, and keywords as JSON."""

        for attempt in range(settings.qie_tier1_max_retries):
            try:
                api_response = await self.client.responses.create(
                    model=settings.qie_tier1_model,
                    input=f"{TIER1_SYSTEM_PROMPT}\n\n{user_prompt}",
                    reasoning={"effort": settings.qie_tier1_reasoning_effort},
                    text={"verbosity": settings.qie_tier1_verbosity},
                )

                output_text = api_response.output_text.strip()

                # Clean JSON if wrapped in markdown
                if output_text.startswith("```"):
                    output_text = output_text.split("```")[1]
                    if output_text.startswith("json"):
                        output_text = output_text[4:]
                    output_text = output_text.strip()

                parsed = json.loads(output_text)

                # Validate and extract fields
                sentiment = max(1, min(10, int(parsed.get("sentiment", 5))))
                category_str = parsed.get("category", "Other")
                keywords = parsed.get("keywords", [])[:5]

                # Map category string to enum
                category = SentimentCategory.OTHER
                for cat in SentimentCategory:
                    if cat.value.lower() == category_str.lower():
                        category = cat
                        break

                return Tier1Result(
                    response_id=persona_id,
                    sentiment=sentiment,
                    category=category,
                    keywords=keywords if isinstance(keywords, list) else [],
                    original_text=response_text[:200],
                    ssr_score=ssr_score,
                )

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                if attempt == settings.qie_tier1_max_retries - 1:
                    # Return fallback on final failure
                    return Tier1Result(
                        response_id=persona_id,
                        sentiment=5,
                        category=SentimentCategory.OTHER,
                        keywords=[],
                        original_text=response_text[:200],
                        ssr_score=ssr_score,
                    )
                await asyncio.sleep(0.5 * (attempt + 1))
            except Exception as e:
                if attempt == settings.qie_tier1_max_retries - 1:
                    return Tier1Result(
                        response_id=persona_id,
                        sentiment=5,
                        category=SentimentCategory.OTHER,
                        keywords=[],
                        original_text=response_text[:200],
                        ssr_score=ssr_score,
                    )
                await asyncio.sleep(1.0 * (attempt + 1))

        # Should not reach here, but fallback just in case
        return Tier1Result(
            response_id=persona_id,
            sentiment=5,
            category=SentimentCategory.OTHER,
            keywords=[],
            original_text=response_text[:200],
            ssr_score=ssr_score,
        )

    def aggregate_tier1_results(
        self,
        tier1_results: list[Tier1Result],
        original_responses: list[dict],
    ) -> AggregatedStats:
        """Aggregate Tier 1 results into statistics for Tier 2."""
        total = len(tier1_results)

        # Sentiment distribution
        sentiment_dist = Counter(r.sentiment for r in tier1_results)

        # Category statistics
        category_groups: dict[str, list[Tier1Result]] = {}
        for result in tier1_results:
            cat_name = result.category.value
            if cat_name not in category_groups:
                category_groups[cat_name] = []
            category_groups[cat_name].append(result)

        category_stats = []
        for cat_name, results in category_groups.items():
            count = len(results)
            avg_sentiment = sum(r.sentiment for r in results) / count if count > 0 else 0
            avg_ssr = sum(r.ssr_score for r in results) / count if count > 0 else 0

            # Get top keywords for this category
            all_keywords = []
            for r in results:
                all_keywords.extend(r.keywords)
            top_keywords = [kw for kw, _ in Counter(all_keywords).most_common(5)]

            category_stats.append(CategoryStats(
                category=cat_name,
                count=count,
                percentage=count / total * 100 if total > 0 else 0,
                avg_sentiment=avg_sentiment,
                avg_ssr=avg_ssr,
                top_keywords=top_keywords,
            ))

        # Sort by count descending
        category_stats.sort(key=lambda x: x.count, reverse=True)

        # Overall keyword frequency
        all_keywords = []
        for r in tier1_results:
            all_keywords.extend(r.keywords)
        keyword_frequency = dict(Counter(all_keywords).most_common(20))

        # Segment breakdown from original responses
        segment_breakdown = self._calculate_segment_breakdown(
            tier1_results, original_responses
        )

        # Separate high/low SSR responses
        low_ssr = [r for r in tier1_results if r.ssr_score < 0.4]
        high_ssr = [r for r in tier1_results if r.ssr_score > 0.7]

        avg_sentiment = sum(r.sentiment for r in tier1_results) / total if total > 0 else 5

        return AggregatedStats(
            total_responses=total,
            avg_sentiment=avg_sentiment,
            sentiment_distribution=dict(sentiment_dist),
            category_stats=category_stats,
            keyword_frequency=keyword_frequency,
            segment_breakdown=segment_breakdown,
            low_ssr_responses=low_ssr[:30],  # Limit for Tier 2 context
            high_ssr_responses=high_ssr[:30],
        )

    def _calculate_segment_breakdown(
        self,
        tier1_results: list[Tier1Result],
        original_responses: list[dict],
    ) -> dict:
        """Calculate statistics by demographic segments."""
        # Create lookup from response_id to tier1 result
        tier1_lookup = {r.response_id: r for r in tier1_results}

        segments = {
            "by_age": {},
            "by_gender": {},
            "by_income": {},
        }

        for response in original_responses:
            persona_id = response.get("persona_id", "")
            demographics = response.get("demographics", {})
            tier1 = tier1_lookup.get(persona_id)

            if not tier1:
                continue

            # Age grouping
            age = demographics.get("age", 0)
            if age < 30:
                age_group = "20대"
            elif age < 40:
                age_group = "30대"
            elif age < 50:
                age_group = "40대"
            else:
                age_group = "50대+"

            if age_group not in segments["by_age"]:
                segments["by_age"][age_group] = {"ssrs": [], "sentiments": []}
            segments["by_age"][age_group]["ssrs"].append(tier1.ssr_score)
            segments["by_age"][age_group]["sentiments"].append(tier1.sentiment)

            # Gender
            gender = demographics.get("gender", "unknown")
            if gender not in segments["by_gender"]:
                segments["by_gender"][gender] = {"ssrs": [], "sentiments": []}
            segments["by_gender"][gender]["ssrs"].append(tier1.ssr_score)
            segments["by_gender"][gender]["sentiments"].append(tier1.sentiment)

            # Income
            income = demographics.get("income", "unknown")
            if income not in segments["by_income"]:
                segments["by_income"][income] = {"ssrs": [], "sentiments": []}
            segments["by_income"][income]["ssrs"].append(tier1.ssr_score)
            segments["by_income"][income]["sentiments"].append(tier1.sentiment)

        # Calculate averages
        result = {}
        for segment_type, groups in segments.items():
            result[segment_type] = {}
            for group_name, data in groups.items():
                ssrs = data["ssrs"]
                sentiments = data["sentiments"]
                result[segment_type][group_name] = {
                    "count": len(ssrs),
                    "avg_ssr": sum(ssrs) / len(ssrs) if ssrs else 0,
                    "avg_sentiment": sum(sentiments) / len(sentiments) if sentiments else 0,
                }

        return result

    async def run_tier2_synthesis(
        self,
        aggregated_stats: AggregatedStats,
        product_description: str,
        original_responses: list[dict],
    ) -> QIEAnalysis:
        """Synthesize insights using gpt-5.2 with medium reasoning effort."""

        # Build context for Tier 2
        stats_summary = self._build_stats_summary(aggregated_stats)

        # Sample quotes from low SSR responses
        low_ssr_quotes = "\n".join([
            f"- [{r.category.value}] (SSR: {r.ssr_score:.2f}) \"{r.original_text}\""
            for r in aggregated_stats.low_ssr_responses[:10]
        ])

        # Sample quotes from high SSR responses
        high_ssr_quotes = "\n".join([
            f"- [{r.category.value}] (SSR: {r.ssr_score:.2f}) \"{r.original_text}\""
            for r in aggregated_stats.high_ssr_responses[:10]
        ])

        user_prompt = f"""## Product Concept
{product_description}

## Aggregated Statistics
{stats_summary}

## Low SSR Responses (Purchase Barriers)
{low_ssr_quotes}

## High SSR Responses (Purchase Drivers)
{high_ssr_quotes}

---
Analyze this data using Key Driver Analysis, Kano Model, and Sentiment Stratification.
Provide actionable insights in the specified format."""

        full_input = f"{TIER2_SYSTEM_PROMPT}\n\n{user_prompt}"

        try:
            response = await self.client.responses.create(
                model=settings.qie_tier2_model,
                input=full_input,
                max_output_tokens=settings.qie_tier2_max_output_tokens,
                reasoning={"effort": settings.qie_tier2_reasoning_effort},
                text={"verbosity": settings.qie_tier2_verbosity},
            )

            analysis_text = response.output_text

            return self._parse_tier2_response(analysis_text, aggregated_stats)

        except Exception as e:
            # Return minimal analysis on error
            return QIEAnalysis(
                executive_summary=f"분석 중 오류 발생: {str(e)}",
                key_drivers=[],
                kano_classification=KanoClassification(
                    must_be_features=[],
                    performance_features=[],
                    delighter_features=[],
                    indifferent_features=[],
                ),
                segment_analysis=SegmentAnalysis(
                    by_age=[],
                    by_gender=[],
                    by_income=[],
                    notable_differences=[],
                ),
                pain_points=[],
                action_items=[],
                confidence_score=0.3,
            )

    def _build_stats_summary(self, stats: AggregatedStats) -> str:
        """Build text summary of aggregated statistics."""
        lines = [
            f"총 응답 수: {stats.total_responses}",
            f"평균 감성 점수: {stats.avg_sentiment:.1f}/10",
            "",
            "### 카테고리별 통계:",
        ]

        for cat in stats.category_stats:
            lines.append(
                f"- {cat.category}: {cat.count}건 ({cat.percentage:.1f}%), "
                f"평균 SSR: {cat.avg_ssr:.2f}, 키워드: {', '.join(cat.top_keywords[:3])}"
            )

        lines.extend([
            "",
            "### 주요 키워드 빈도:",
            ", ".join([f"{kw}({count})" for kw, count in list(stats.keyword_frequency.items())[:10]]),
            "",
            "### 세그먼트별 SSR:",
        ])

        for segment_type, groups in stats.segment_breakdown.items():
            segment_name = {"by_age": "연령", "by_gender": "성별", "by_income": "소득"}.get(segment_type, segment_type)
            group_strs = [f"{name}: {data['avg_ssr']:.2f}" for name, data in groups.items()]
            lines.append(f"- {segment_name}: {', '.join(group_strs)}")

        return "\n".join(lines)

    def _parse_tier2_response(
        self,
        analysis_text: str,
        aggregated_stats: AggregatedStats,
    ) -> QIEAnalysis:
        """Parse Tier 2 markdown response into structured QIEAnalysis."""

        # Extract sections
        sections = self._split_markdown_sections(analysis_text)

        # Executive Summary
        executive_summary = sections.get("executive summary", sections.get("요약", ""))
        if not executive_summary:
            # Try to get first meaningful paragraph
            lines = analysis_text.split("\n")
            for line in lines:
                if line.strip() and not line.startswith("#"):
                    executive_summary = line.strip()
                    break

        # Key Drivers
        key_drivers = self._extract_key_drivers(
            sections.get("key drivers", sections.get("핵심 요인", "")),
            aggregated_stats
        )

        # Kano Classification
        kano = self._extract_kano_classification(
            sections.get("kano", sections.get("카노", ""))
        )

        # Segment Analysis
        segment_analysis = self._extract_segment_analysis(
            sections.get("segment", sections.get("세그먼트", "")),
            aggregated_stats
        )

        # Pain Points
        pain_points = self._extract_pain_points(
            sections.get("pain point", sections.get("문제점", "")),
            aggregated_stats
        )

        # Action Items
        action_items = self._extract_action_items(
            sections.get("action", sections.get("실행", ""))
        )

        return QIEAnalysis(
            executive_summary=executive_summary,
            key_drivers=key_drivers,
            kano_classification=kano,
            segment_analysis=segment_analysis,
            pain_points=pain_points,
            action_items=action_items,
            confidence_score=0.8,
            analysis_metadata={"raw_text_length": len(analysis_text)},
        )

    def _split_markdown_sections(self, text: str) -> dict[str, str]:
        """Split markdown text into sections by headers."""
        sections = {}
        current_section = ""
        current_content = []

        for line in text.split("\n"):
            if line.startswith("##"):
                if current_section:
                    sections[current_section.lower()] = "\n".join(current_content)
                current_section = line.lstrip("#").strip()
                current_content = []
            else:
                current_content.append(line)

        if current_section:
            sections[current_section.lower()] = "\n".join(current_content)

        return sections

    def _extract_key_drivers(
        self,
        section_text: str,
        stats: AggregatedStats,
    ) -> list[KeyDriver]:
        """Extract key drivers from analysis text."""
        drivers = []

        # Extract from category stats as fallback/supplement
        for cat in stats.category_stats:
            if cat.count >= 5:  # Minimum sample
                impact = ImpactDirection.POSITIVE if cat.avg_ssr > 0.5 else ImpactDirection.NEGATIVE
                correlation = (cat.avg_ssr - 0.5) * 2  # Scale to -1 to 1

                drivers.append(KeyDriver(
                    factor=cat.category,
                    impact=impact,
                    correlation=correlation,
                    description=f"{cat.category} 관련 응답 {cat.count}건, 평균 SSR {cat.avg_ssr:.2f}",
                    evidence_count=cat.count,
                    example_quotes=[],
                ))

        # Parse any additional drivers from text
        lines = section_text.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("-") or line.startswith("•"):
                # Simple parsing - could be enhanced
                factor = line.lstrip("-•").strip()
                if factor and len(factor) > 5:
                    # Check if already exists
                    existing = [d for d in drivers if d.factor.lower() in factor.lower()]
                    if not existing:
                        impact = ImpactDirection.NEGATIVE if any(
                            word in factor.lower()
                            for word in ["부정", "negative", "barrier", "장벽", "문제"]
                        ) else ImpactDirection.POSITIVE

                        drivers.append(KeyDriver(
                            factor=factor[:50],
                            impact=impact,
                            correlation=0.0,
                            description=factor,
                            evidence_count=0,
                        ))

        return drivers[:10]  # Limit to top 10

    def _extract_kano_classification(self, section_text: str) -> KanoClassification:
        """Extract Kano model classification from analysis text."""
        must_be = []
        performance = []
        delighter = []
        indifferent = []

        current_category = None
        lines = section_text.split("\n")

        for line in lines:
            line_lower = line.lower()

            if "must" in line_lower or "기본" in line_lower or "필수" in line_lower:
                current_category = "must_be"
            elif "performance" in line_lower or "성능" in line_lower or "일차원" in line_lower:
                current_category = "performance"
            elif "delighter" in line_lower or "매력" in line_lower or "감동" in line_lower:
                current_category = "delighter"
            elif "indifferent" in line_lower or "무관심" in line_lower:
                current_category = "indifferent"
            elif line.strip().startswith("-") or line.strip().startswith("•"):
                feature_name = line.lstrip("-•").strip()
                if feature_name and current_category:
                    # Map category string to enum and list
                    category_map = {
                        "must_be": (KanoCategory.MUST_BE, must_be),
                        "performance": (KanoCategory.PERFORMANCE, performance),
                        "delighter": (KanoCategory.DELIGHTER, delighter),
                        "indifferent": (KanoCategory.INDIFFERENT, indifferent),
                    }

                    if current_category in category_map:
                        kano_category, feature_list = category_map[current_category]
                        feature = KanoFeature(
                            feature_name=feature_name[:50],
                            category=kano_category,
                            satisfaction_impact=0.5,
                            mention_count=0,
                            description=feature_name,
                        )
                        feature_list.append(feature)

        return KanoClassification(
            must_be_features=must_be,
            performance_features=performance,
            delighter_features=delighter,
            indifferent_features=indifferent,
        )

    def _extract_segment_analysis(
        self,
        section_text: str,
        stats: AggregatedStats,
    ) -> SegmentAnalysis:
        """Extract segment analysis from stats and text."""
        by_age = []
        by_gender = []
        by_income = []

        # Build from aggregated stats
        segment_data = stats.segment_breakdown

        for age_group, data in segment_data.get("by_age", {}).items():
            by_age.append(SegmentInsight(
                segment_name="연령",
                segment_value=age_group,
                sample_size=data.get("count", 0),
                avg_ssr=data.get("avg_ssr", 0),
                avg_sentiment=data.get("avg_sentiment", 0),
                top_concerns=[],
                key_preferences=[],
            ))

        for gender, data in segment_data.get("by_gender", {}).items():
            by_gender.append(SegmentInsight(
                segment_name="성별",
                segment_value=gender,
                sample_size=data.get("count", 0),
                avg_ssr=data.get("avg_ssr", 0),
                avg_sentiment=data.get("avg_sentiment", 0),
                top_concerns=[],
                key_preferences=[],
            ))

        for income, data in segment_data.get("by_income", {}).items():
            by_income.append(SegmentInsight(
                segment_name="소득",
                segment_value=income,
                sample_size=data.get("count", 0),
                avg_ssr=data.get("avg_ssr", 0),
                avg_sentiment=data.get("avg_sentiment", 0),
                top_concerns=[],
                key_preferences=[],
            ))

        # Extract notable differences from text
        notable = []
        for line in section_text.split("\n"):
            if line.strip() and not line.startswith("#"):
                notable.append(line.strip()[:100])

        return SegmentAnalysis(
            by_age=by_age,
            by_gender=by_gender,
            by_income=by_income,
            notable_differences=notable[:5],
        )

    def _extract_pain_points(
        self,
        section_text: str,
        stats: AggregatedStats,
    ) -> list[PainPoint]:
        """Extract pain points from analysis."""
        pain_points = []

        # Build from low SSR category stats
        for cat in stats.category_stats:
            if cat.avg_ssr < 0.5:
                severity = (1 - cat.avg_ssr) * 100  # Convert to 0-100
                pain_points.append(PainPoint(
                    category=SentimentCategory(cat.category) if cat.category in [c.value for c in SentimentCategory] else SentimentCategory.OTHER,
                    score=severity,
                    description=f"{cat.category} 관련 문제: 평균 SSR {cat.avg_ssr:.2f}",
                    affected_percentage=cat.percentage,
                    example_quotes=[r.original_text for r in stats.low_ssr_responses if r.category.value == cat.category][:3],
                ))

        # Sort by severity
        pain_points.sort(key=lambda x: x.score, reverse=True)

        return pain_points[:5]

    def _extract_action_items(self, section_text: str) -> list[ActionItem]:
        """Extract action items from analysis text."""
        items = []
        current_priority = ActionPriority.MEDIUM

        for line in section_text.split("\n"):
            line_lower = line.lower()

            # Detect priority markers
            if "immediate" in line_lower or "즉시" in line_lower or "긴급" in line_lower:
                current_priority = ActionPriority.IMMEDIATE
            elif "high" in line_lower or "높음" in line_lower:
                current_priority = ActionPriority.HIGH
            elif "medium" in line_lower or "중간" in line_lower:
                current_priority = ActionPriority.MEDIUM
            elif "low" in line_lower or "낮음" in line_lower:
                current_priority = ActionPriority.LOW

            # Extract action items
            if line.strip().startswith("-") or line.strip().startswith("•") or line.strip().startswith("1"):
                title = line.lstrip("-•0123456789.").strip()
                if title and len(title) > 5:
                    items.append(ActionItem(
                        title=title[:80],
                        description=title,
                        priority=current_priority,
                        category="general",
                        expected_impact="개선 예상",
                    ))

        # Sort by priority
        priority_order = {
            ActionPriority.IMMEDIATE: 0,
            ActionPriority.HIGH: 1,
            ActionPriority.MEDIUM: 2,
            ActionPriority.LOW: 3,
        }
        items.sort(key=lambda x: priority_order.get(x.priority, 2))

        return items[:10]


def tier1_result_to_dict(result: Tier1Result) -> dict:
    """Convert Tier1Result to dictionary for JSON serialization."""
    return {
        "response_id": result.response_id,
        "sentiment": result.sentiment,
        "category": result.category.value,
        "keywords": result.keywords,
        "original_text": result.original_text,
        "ssr_score": result.ssr_score,
    }


def aggregated_stats_to_dict(stats: AggregatedStats) -> dict:
    """Convert AggregatedStats to dictionary for JSON serialization."""
    return {
        "total_responses": stats.total_responses,
        "avg_sentiment": stats.avg_sentiment,
        "sentiment_distribution": stats.sentiment_distribution,
        "category_stats": [
            {
                "category": cs.category,
                "count": cs.count,
                "percentage": cs.percentage,
                "avg_sentiment": cs.avg_sentiment,
                "avg_ssr": cs.avg_ssr,
                "top_keywords": cs.top_keywords,
            }
            for cs in stats.category_stats
        ],
        "keyword_frequency": stats.keyword_frequency,
        "segment_breakdown": stats.segment_breakdown,
        "low_ssr_count": len(stats.low_ssr_responses),
        "high_ssr_count": len(stats.high_ssr_responses),
    }


def qie_analysis_to_dict(analysis: QIEAnalysis) -> dict:
    """Convert QIEAnalysis to dictionary for JSON serialization."""
    return {
        "executive_summary": analysis.executive_summary,
        "key_drivers": [
            {
                "factor": kd.factor,
                "impact": kd.impact.value,
                "correlation": kd.correlation,
                "description": kd.description,
                "evidence_count": kd.evidence_count,
                "example_quotes": kd.example_quotes,
            }
            for kd in analysis.key_drivers
        ],
        "kano_classification": {
            "must_be_features": [
                {
                    "feature_name": f.feature_name,
                    "category": f.category.value,
                    "satisfaction_impact": f.satisfaction_impact,
                    "mention_count": f.mention_count,
                    "description": f.description,
                }
                for f in analysis.kano_classification.must_be_features
            ],
            "performance_features": [
                {
                    "feature_name": f.feature_name,
                    "category": f.category.value,
                    "satisfaction_impact": f.satisfaction_impact,
                    "mention_count": f.mention_count,
                    "description": f.description,
                }
                for f in analysis.kano_classification.performance_features
            ],
            "delighter_features": [
                {
                    "feature_name": f.feature_name,
                    "category": f.category.value,
                    "satisfaction_impact": f.satisfaction_impact,
                    "mention_count": f.mention_count,
                    "description": f.description,
                }
                for f in analysis.kano_classification.delighter_features
            ],
            "indifferent_features": [
                {
                    "feature_name": f.feature_name,
                    "category": f.category.value,
                    "satisfaction_impact": f.satisfaction_impact,
                    "mention_count": f.mention_count,
                    "description": f.description,
                }
                for f in analysis.kano_classification.indifferent_features
            ],
        },
        "segment_analysis": {
            "by_age": [
                {
                    "segment_name": s.segment_name,
                    "segment_value": s.segment_value,
                    "sample_size": s.sample_size,
                    "avg_ssr": s.avg_ssr,
                    "avg_sentiment": s.avg_sentiment,
                    "top_concerns": s.top_concerns,
                    "key_preferences": s.key_preferences,
                }
                for s in analysis.segment_analysis.by_age
            ],
            "by_gender": [
                {
                    "segment_name": s.segment_name,
                    "segment_value": s.segment_value,
                    "sample_size": s.sample_size,
                    "avg_ssr": s.avg_ssr,
                    "avg_sentiment": s.avg_sentiment,
                    "top_concerns": s.top_concerns,
                    "key_preferences": s.key_preferences,
                }
                for s in analysis.segment_analysis.by_gender
            ],
            "by_income": [
                {
                    "segment_name": s.segment_name,
                    "segment_value": s.segment_value,
                    "sample_size": s.sample_size,
                    "avg_ssr": s.avg_ssr,
                    "avg_sentiment": s.avg_sentiment,
                    "top_concerns": s.top_concerns,
                    "key_preferences": s.key_preferences,
                }
                for s in analysis.segment_analysis.by_income
            ],
            "notable_differences": analysis.segment_analysis.notable_differences,
        },
        "pain_points": [
            {
                "category": pp.category.value,
                "score": pp.score,
                "description": pp.description,
                "affected_percentage": pp.affected_percentage,
                "example_quotes": pp.example_quotes,
            }
            for pp in analysis.pain_points
        ],
        "action_items": [
            {
                "title": ai.title,
                "description": ai.description,
                "priority": ai.priority.value,
                "category": ai.category,
                "expected_impact": ai.expected_impact,
                "related_pain_points": ai.related_pain_points,
            }
            for ai in analysis.action_items
        ],
        "confidence_score": analysis.confidence_score,
        "analysis_metadata": analysis.analysis_metadata,
    }
