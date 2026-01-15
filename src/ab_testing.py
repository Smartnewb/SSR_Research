"""A/B testing module for comparing product concepts."""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats

from .pipeline import SSRPipeline
from .reporting.aggregator import AggregatedResults


@dataclass
class ABTestResult:
    """Results from an A/B comparison test."""

    product_a_name: str
    product_b_name: str
    results_a: AggregatedResults
    results_b: AggregatedResults
    mean_difference: float
    relative_difference: float
    t_statistic: float
    p_value: float
    confidence_interval: tuple[float, float]
    winner: Optional[str]
    significant: bool
    effect_size: float

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"A/B Test Results: {self.product_a_name} vs {self.product_b_name}",
            "=" * 60,
            "",
            f"Product A ({self.product_a_name}):",
            f"  Mean Score: {self.results_a.mean_score:.3f}",
            f"  Std Dev: {self.results_a.std_dev:.3f}",
            f"  Sample Size: {self.results_a.sample_size}",
            "",
            f"Product B ({self.product_b_name}):",
            f"  Mean Score: {self.results_b.mean_score:.3f}",
            f"  Std Dev: {self.results_b.std_dev:.3f}",
            f"  Sample Size: {self.results_b.sample_size}",
            "",
            "Statistical Analysis:",
            f"  Mean Difference (A - B): {self.mean_difference:+.3f}",
            f"  Relative Difference: {self.relative_difference:+.1%}",
            f"  Effect Size (Cohen's d): {self.effect_size:.3f}",
            f"  t-statistic: {self.t_statistic:.3f}",
            f"  p-value: {self.p_value:.4f}",
            f"  95% CI: [{self.confidence_interval[0]:.3f}, {self.confidence_interval[1]:.3f}]",
            "",
        ]

        if self.significant:
            lines.append(f"WINNER: {self.winner} (statistically significant, p < 0.05)")
        else:
            lines.append("No statistically significant difference detected.")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "product_a": {
                "name": self.product_a_name,
                "mean_score": self.results_a.mean_score,
                "std_dev": self.results_a.std_dev,
                "sample_size": self.results_a.sample_size,
                "total_cost": self.results_a.total_cost,
            },
            "product_b": {
                "name": self.product_b_name,
                "mean_score": self.results_b.mean_score,
                "std_dev": self.results_b.std_dev,
                "sample_size": self.results_b.sample_size,
                "total_cost": self.results_b.total_cost,
            },
            "analysis": {
                "mean_difference": self.mean_difference,
                "relative_difference": self.relative_difference,
                "t_statistic": self.t_statistic,
                "p_value": self.p_value,
                "confidence_interval": list(self.confidence_interval),
                "effect_size": self.effect_size,
                "significant": self.significant,
                "winner": self.winner,
            },
        }


def calculate_cohens_d(mean_a: float, mean_b: float, std_a: float, std_b: float) -> float:
    """Calculate Cohen's d effect size."""
    pooled_std = np.sqrt((std_a**2 + std_b**2) / 2)
    if pooled_std == 0:
        return 0.0
    return (mean_a - mean_b) / pooled_std


def run_ab_test(
    product_a: str,
    product_b: str,
    sample_size: int = 50,
    product_a_name: str = "Product A",
    product_b_name: str = "Product B",
    llm_model: str = "gpt-4o-mini",
    target_demographics: Optional[dict] = None,
    significance_level: float = 0.05,
    use_mock: bool = False,
    show_progress: bool = True,
) -> ABTestResult:
    """
    Run an A/B test comparing two product concepts.

    Args:
        product_a: Description of first product
        product_b: Description of second product
        sample_size: Number of respondents per product
        product_a_name: Display name for product A
        product_b_name: Display name for product B
        llm_model: LLM model to use
        target_demographics: Optional demographic filters
        significance_level: Alpha level for statistical test
        use_mock: Whether to use mock data
        show_progress: Whether to display progress bars

    Returns:
        ABTestResult with comparison statistics
    """
    pipeline = SSRPipeline(llm_model=llm_model)

    if use_mock:
        results_a = pipeline.run_survey_mock(
            product_description=product_a,
            sample_size=sample_size,
            show_progress=show_progress,
        )
        results_b = pipeline.run_survey_mock(
            product_description=product_b,
            sample_size=sample_size,
            show_progress=show_progress,
        )
    else:
        results_a = pipeline.run_survey(
            product_description=product_a,
            sample_size=sample_size,
            target_demographics=target_demographics,
            show_progress=show_progress,
        )
        results_b = pipeline.run_survey(
            product_description=product_b,
            sample_size=sample_size,
            target_demographics=target_demographics,
            show_progress=show_progress,
        )

    scores_a = [r.ssr_score for r in results_a.results]
    scores_b = [r.ssr_score for r in results_b.results]

    t_stat, p_value = stats.ttest_ind(scores_a, scores_b)

    mean_diff = results_a.mean_score - results_b.mean_score

    if results_b.mean_score > 0:
        relative_diff = mean_diff / results_b.mean_score
    else:
        relative_diff = 0.0

    se = np.sqrt(
        (results_a.std_dev**2 / len(scores_a)) +
        (results_b.std_dev**2 / len(scores_b))
    )
    ci_margin = 1.96 * se
    ci = (mean_diff - ci_margin, mean_diff + ci_margin)

    effect_size = calculate_cohens_d(
        results_a.mean_score,
        results_b.mean_score,
        results_a.std_dev,
        results_b.std_dev,
    )

    significant = p_value < significance_level
    if significant:
        winner = product_a_name if mean_diff > 0 else product_b_name
    else:
        winner = None

    return ABTestResult(
        product_a_name=product_a_name,
        product_b_name=product_b_name,
        results_a=results_a,
        results_b=results_b,
        mean_difference=mean_diff,
        relative_difference=relative_diff,
        t_statistic=float(t_stat),
        p_value=float(p_value),
        confidence_interval=ci,
        winner=winner,
        significant=significant,
        effect_size=abs(effect_size),
    )


def run_ab_test_mock(
    product_a: str,
    product_b: str,
    sample_size: int = 20,
    product_a_name: str = "Product A",
    product_b_name: str = "Product B",
    mock_responses_a: Optional[list[str]] = None,
    mock_responses_b: Optional[list[str]] = None,
) -> ABTestResult:
    """Run A/B test with mock data for testing."""
    return run_ab_test(
        product_a=product_a,
        product_b=product_b,
        sample_size=sample_size,
        product_a_name=product_a_name,
        product_b_name=product_b_name,
        use_mock=True,
        show_progress=False,
    )
