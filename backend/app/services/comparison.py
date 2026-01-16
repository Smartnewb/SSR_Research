"""Multi-concept comparison service."""

import asyncio
from typing import List, Dict, Tuple
import numpy as np
from scipy import stats

from ..models.comparison import (
    ConceptInput,
    AbsoluteScore,
    DistributionStats,
    RelativePreference,
    PreferenceMatrixEntry,
    StatisticalSignificance,
    SegmentAnalysis,
    ComparisonResults,
)


async def run_multi_concept_comparison(
    concepts: List[ConceptInput],
    personas: List[dict],
    comparison_mode: str,
    use_mock: bool = False,
) -> ComparisonResults:
    """
    Run SSR survey for multiple concepts and compare results.

    Args:
        concepts: List of 2-5 product concepts to compare
        personas: List of persona dicts with demographics and system prompts
        comparison_mode: "rank_based" or "absolute"
        use_mock: Use mock responses for testing

    Returns:
        ComparisonResults with absolute scores, relative preference, significance
    """
    # 1. Run surveys in parallel for all concepts
    survey_tasks = [
        run_ssr_survey_for_concept(concept, personas, use_mock)
        for concept in concepts
    ]
    survey_results = await asyncio.gather(*survey_tasks)

    # 2. Calculate absolute scores
    absolute_scores = [
        calculate_absolute_score(concepts[i], survey_results[i])
        for i in range(len(concepts))
    ]

    # 3. Calculate relative preference (if rank_based)
    relative_preference = None
    if comparison_mode == "rank_based":
        relative_preference = calculate_pairwise_preference(concepts, survey_results)

    # 4. Statistical significance testing
    significance = calculate_statistical_significance(concepts, survey_results)

    # 5. Segment analysis
    segment_analysis = analyze_by_segments(concepts, survey_results, personas)

    # 6. Extract key differentiators (LLM-based)
    differentiators = await extract_key_differentiators(
        concepts, absolute_scores, use_mock
    )

    return ComparisonResults(
        absolute_scores=absolute_scores,
        relative_preference=relative_preference,
        statistical_significance=significance,
        segment_analysis=segment_analysis,
        key_differentiators=differentiators,
    )


async def run_ssr_survey_for_concept(
    concept: ConceptInput, personas: List[dict], use_mock: bool = False
) -> List[float]:
    """
    Run SSR survey for a single concept across all personas.

    Returns:
        List of SSR scores (0.0-1.0) for each persona
    """
    if use_mock:
        # Mock responses for testing
        return generate_mock_ssr_scores(len(personas), base_score=0.7)

    from .surveys import run_ssr_for_persona  # Avoid circular import

    # Run surveys in parallel (batches of 10 to avoid rate limits)
    batch_size = 10
    all_scores = []

    for i in range(0, len(personas), batch_size):
        batch = personas[i : i + batch_size]
        batch_tasks = [
            run_ssr_for_persona(concept_to_description(concept), persona)
            for persona in batch
        ]
        batch_scores = await asyncio.gather(*batch_tasks)
        all_scores.extend(batch_scores)

    return all_scores


def concept_to_description(concept: ConceptInput) -> str:
    """Convert ConceptInput to product description string."""
    return f"""
Product: {concept.title}

{concept.headline}

Consumer Insight: {concept.consumer_insight}

Key Benefit: {concept.benefit}

Reason to Believe: {concept.rtb}

Product Description: {concept.image_description}

Price: {concept.price}
""".strip()


def generate_mock_ssr_scores(n: int, base_score: float = 0.7) -> List[float]:
    """Generate mock SSR scores for testing."""
    # Normal distribution around base_score
    scores = np.random.normal(base_score, 0.15, n)
    # Clip to [0, 1]
    scores = np.clip(scores, 0.0, 1.0)
    return scores.tolist()


def calculate_absolute_score(
    concept: ConceptInput, scores: List[float]
) -> AbsoluteScore:
    """Calculate absolute SSR score statistics for a concept."""
    scores_array = np.array(scores)

    mean_ssr = float(np.mean(scores_array))
    std_dev = float(np.std(scores_array))
    median_ssr = float(np.median(scores_array))

    # Calculate distribution
    definitely_buy = float(np.mean((scores_array >= 0.8) & (scores_array <= 1.0)))
    probably_buy = float(np.mean((scores_array >= 0.6) & (scores_array < 0.8)))
    maybe = float(np.mean((scores_array >= 0.4) & (scores_array < 0.6)))
    unlikely = float(np.mean((scores_array >= 0.0) & (scores_array < 0.4)))

    return AbsoluteScore(
        concept_id=concept.id,
        concept_title=concept.title,
        mean_ssr=mean_ssr,
        std_dev=std_dev,
        median_ssr=median_ssr,
        distribution=DistributionStats(
            definitely_buy=definitely_buy,
            probably_buy=probably_buy,
            maybe=maybe,
            unlikely=unlikely,
        ),
    )


def calculate_pairwise_preference(
    concepts: List[ConceptInput], survey_results: List[List[float]]
) -> RelativePreference:
    """
    Calculate pairwise preference rates.

    For each persona, rank concepts by SSR score.
    Count how many times concept_a beats concept_b.
    """
    n_concepts = len(concepts)
    n_personas = len(survey_results[0])

    # Create preference count matrix
    preference_counts = np.zeros((n_concepts, n_concepts))

    for persona_idx in range(n_personas):
        # Get scores for this persona across all concepts
        scores = [survey_results[c][persona_idx] for c in range(n_concepts)]

        # Compare all pairs
        for i in range(n_concepts):
            for j in range(n_concepts):
                if i != j and scores[i] > scores[j]:
                    preference_counts[i][j] += 1

    # Normalize to percentages
    preference_matrix = preference_counts / n_personas

    # Build preference matrix entries
    entries = []
    for i in range(n_concepts):
        for j in range(n_concepts):
            if i != j:
                entries.append(
                    PreferenceMatrixEntry(
                        concept_a=concepts[i].id,
                        concept_b=concepts[j].id,
                        preference_rate=float(preference_matrix[i][j]),
                    )
                )

    # Determine winner (concept with highest total win rate)
    total_win_rates = np.sum(preference_matrix, axis=1)
    winner_idx = int(np.argmax(total_win_rates))

    return RelativePreference(
        winner=concepts[winner_idx].id,
        preference_matrix=entries,
    )


def calculate_statistical_significance(
    concepts: List[ConceptInput], survey_results: List[List[float]]
) -> StatisticalSignificance:
    """
    Calculate statistical significance using t-test (2 concepts) or ANOVA (3+).
    """
    n_concepts = len(concepts)

    if n_concepts == 2:
        # Two-sample t-test
        scores_a = survey_results[0]
        scores_b = survey_results[1]

        t_stat, p_value = stats.ttest_ind(scores_a, scores_b)

        is_significant = p_value < 0.05
        mean_a = np.mean(scores_a)
        mean_b = np.mean(scores_b)

        if is_significant:
            if mean_a > mean_b:
                interpretation = (
                    f"{concepts[0].title} significantly outperforms {concepts[1].title} "
                    f"(p={p_value:.4f}, mean diff={mean_a - mean_b:.3f})"
                )
            else:
                interpretation = (
                    f"{concepts[1].title} significantly outperforms {concepts[0].title} "
                    f"(p={p_value:.4f}, mean diff={mean_b - mean_a:.3f})"
                )
        else:
            interpretation = (
                f"No significant difference between concepts (p={p_value:.4f})"
            )

        return StatisticalSignificance(
            test_type="t_test",
            statistic=float(t_stat),
            p_value=float(p_value),
            is_significant=is_significant,
            confidence_level=0.95,
            interpretation=interpretation,
        )

    else:
        # One-way ANOVA for 3+ concepts
        f_stat, p_value = stats.f_oneway(*survey_results)

        is_significant = p_value < 0.05

        if is_significant:
            # Find best performing concept
            means = [np.mean(scores) for scores in survey_results]
            best_idx = int(np.argmax(means))
            interpretation = (
                f"Significant differences detected among concepts (p={p_value:.4f}). "
                f"{concepts[best_idx].title} has highest mean SSR ({means[best_idx]:.3f})"
            )
        else:
            interpretation = (
                f"No significant differences among concepts (p={p_value:.4f})"
            )

        return StatisticalSignificance(
            test_type="anova",
            statistic=float(f_stat),
            p_value=float(p_value),
            is_significant=is_significant,
            confidence_level=0.95,
            interpretation=interpretation,
        )


def analyze_by_segments(
    concepts: List[ConceptInput],
    survey_results: List[List[float]],
    personas: List[dict],
) -> List[SegmentAnalysis]:
    """
    Analyze winners by demographic segments.

    Segments: age_18_30, age_30_40, age_40_50, high_income, mid_income, low_income
    """
    segments = []

    # Age segments
    age_segments = [
        ("age_18_30", lambda p: 18 <= p.get("age", 0) < 30),
        ("age_30_40", lambda p: 30 <= p.get("age", 0) < 40),
        ("age_40_50", lambda p: 40 <= p.get("age", 0) < 50),
        ("age_50_plus", lambda p: p.get("age", 0) >= 50),
    ]

    # Income segments
    income_segments = [
        ("high_income", lambda p: p.get("income_bracket") == "high"),
        ("mid_income", lambda p: p.get("income_bracket") == "mid"),
        ("low_income", lambda p: p.get("income_bracket") == "low"),
        ("no_income", lambda p: p.get("income_bracket") == "none"),
    ]

    all_segments = age_segments + income_segments

    for segment_name, segment_filter in all_segments:
        # Find personas in this segment
        segment_indices = [
            i for i, persona in enumerate(personas) if segment_filter(persona)
        ]

        if len(segment_indices) < 10:  # Skip segments with too few personas
            continue

        # Calculate mean SSR for each concept in this segment
        concept_means = []
        for concept_idx in range(len(concepts)):
            segment_scores = [
                survey_results[concept_idx][i] for i in segment_indices
            ]
            concept_means.append((concepts[concept_idx].id, np.mean(segment_scores)))

        # Sort by mean SSR
        concept_means.sort(key=lambda x: x[1], reverse=True)

        winner_id, winner_mean = concept_means[0]
        runner_up_id, runner_up_mean = concept_means[1]

        segments.append(
            SegmentAnalysis(
                segment=segment_name,
                segment_size=len(segment_indices),
                winner=winner_id,
                winner_mean_ssr=float(winner_mean),
                runner_up=runner_up_id,
                runner_up_mean_ssr=float(runner_up_mean),
                mean_diff=float(winner_mean - runner_up_mean),
            )
        )

    return segments


async def extract_key_differentiators(
    concepts: List[ConceptInput],
    absolute_scores: List[AbsoluteScore],
    use_mock: bool = False,
) -> List[str]:
    """
    Use LLM to identify key differentiators between concepts.
    """
    if use_mock:
        return [
            "Price positioning: Lower-priced concepts perform better in mid-income segment",
            "Speed claims: '3-day results' messaging resonates strongly with time-sensitive buyers",
            "Sensitivity concerns: Concepts addressing dental sensitivity win high-usage customers",
        ]

    from anthropic import Anthropic

    client = Anthropic()

    # Prepare comparison data
    comparison_text = "\n\n".join(
        [
            f"**Concept {i+1}: {concept.title}**\n"
            f"- Headline: {concept.headline}\n"
            f"- Price: {concept.price}\n"
            f"- Mean SSR: {score.mean_ssr:.3f}\n"
            f"- Top Segment: Definitely Buy {score.distribution.definitely_buy:.1%}"
            for i, (concept, score) in enumerate(zip(concepts, absolute_scores))
        ]
    )

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""Analyze these product concepts and identify 3-5 key differentiators that explain performance differences:

{comparison_text}

Focus on:
1. Price positioning and value perception
2. Messaging effectiveness (headlines, claims)
3. Feature appeal (benefits, RTBs)
4. Demographic fit

Output as a bullet list of key differentiators with brief explanations.""",
            }
        ],
    )

    # Parse bullet points
    text = response.content[0].text
    differentiators = [
        line.strip("- ").strip() for line in text.split("\n") if line.strip().startswith("-")
    ]

    return differentiators[:5]
