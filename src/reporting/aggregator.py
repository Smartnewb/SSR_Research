"""Results aggregation and statistical analysis."""

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class SurveyResult:
    """Result from a single survey respondent."""

    persona_id: str
    response_text: str
    ssr_score: float
    persona_data: Optional[dict] = None
    tokens_used: int = 0
    cost: float = 0.0
    latency_ms: int = 0


@dataclass
class AggregatedResults:
    """Aggregated results from a survey."""

    results: list[SurveyResult]
    mean_score: float
    median_score: float
    std_dev: float
    min_score: float
    max_score: float
    total_cost: float
    total_tokens: int
    avg_latency_ms: float
    sample_size: int
    score_distribution: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "mean_score": self.mean_score,
            "median_score": self.median_score,
            "std_dev": self.std_dev,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "avg_latency_ms": self.avg_latency_ms,
            "sample_size": self.sample_size,
            "score_distribution": self.score_distribution,
        }


def calculate_statistics(scores: list[float]) -> dict:
    """
    Calculate basic statistics for a list of scores.

    Args:
        scores: List of SSR scores

    Returns:
        Dictionary with mean, median, std_dev, min, max
    """
    if not scores:
        return {
            "mean": 0.0,
            "median": 0.0,
            "std_dev": 0.0,
            "min": 0.0,
            "max": 0.0,
        }

    arr = np.array(scores)
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std_dev": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def calculate_distribution(scores: list[float], bins: int = 10) -> dict:
    """
    Calculate score distribution histogram.

    Args:
        scores: List of SSR scores
        bins: Number of histogram bins

    Returns:
        Dictionary mapping bin labels to counts
    """
    if not scores:
        return {}

    counts, bin_edges = np.histogram(scores, bins=bins, range=(0, 1))

    distribution = {}
    for i, count in enumerate(counts):
        label = f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}"
        distribution[label] = int(count)

    return distribution


def aggregate_results(results: list[SurveyResult]) -> AggregatedResults:
    """
    Aggregate survey results into summary statistics.

    Args:
        results: List of individual survey results

    Returns:
        AggregatedResults with statistics
    """
    if not results:
        return AggregatedResults(
            results=[],
            mean_score=0.0,
            median_score=0.0,
            std_dev=0.0,
            min_score=0.0,
            max_score=0.0,
            total_cost=0.0,
            total_tokens=0,
            avg_latency_ms=0.0,
            sample_size=0,
            score_distribution={},
        )

    scores = [r.ssr_score for r in results]
    stats = calculate_statistics(scores)
    distribution = calculate_distribution(scores)

    total_cost = sum(r.cost for r in results)
    total_tokens = sum(r.tokens_used for r in results)
    avg_latency = (
        sum(r.latency_ms for r in results) / len(results) if results else 0.0
    )

    return AggregatedResults(
        results=results,
        mean_score=stats["mean"],
        median_score=stats["median"],
        std_dev=stats["std_dev"],
        min_score=stats["min"],
        max_score=stats["max"],
        total_cost=total_cost,
        total_tokens=total_tokens,
        avg_latency_ms=avg_latency,
        sample_size=len(results),
        score_distribution=distribution,
    )


def get_top_responses(
    results: list[SurveyResult],
    n: int = 5,
    high: bool = True,
) -> list[SurveyResult]:
    """
    Get top or bottom N responses by score.

    Args:
        results: List of survey results
        n: Number of responses to return
        high: If True, return highest scores; if False, lowest

    Returns:
        List of top/bottom results
    """
    sorted_results = sorted(
        results,
        key=lambda r: r.ssr_score,
        reverse=high,
    )
    return sorted_results[:n]


@dataclass
class ABTestResult:
    """Result from A/B test comparison."""

    product_a_name: str
    product_b_name: str
    results_a: AggregatedResults
    results_b: AggregatedResults
    mean_diff: float
    relative_diff_pct: float
    winner: str
    confidence: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "product_a": {
                "name": self.product_a_name,
                "mean_score": self.results_a.mean_score,
                "std_dev": self.results_a.std_dev,
                "sample_size": self.results_a.sample_size,
            },
            "product_b": {
                "name": self.product_b_name,
                "mean_score": self.results_b.mean_score,
                "std_dev": self.results_b.std_dev,
                "sample_size": self.results_b.sample_size,
            },
            "comparison": {
                "mean_diff": self.mean_diff,
                "relative_diff_pct": self.relative_diff_pct,
                "winner": self.winner,
                "confidence": self.confidence,
            },
        }


def compare_ab_results(
    results_a: AggregatedResults,
    results_b: AggregatedResults,
    name_a: str = "Product A",
    name_b: str = "Product B",
) -> ABTestResult:
    """
    Compare two survey results for A/B testing.

    Args:
        results_a: Results for product A
        results_b: Results for product B
        name_a: Name for product A
        name_b: Name for product B

    Returns:
        ABTestResult with comparison metrics
    """
    mean_diff = results_a.mean_score - results_b.mean_score
    base = results_b.mean_score if results_b.mean_score != 0 else 1.0
    relative_diff_pct = (mean_diff / base) * 100

    if abs(mean_diff) < 0.02:
        winner = "Tie"
        confidence = "Low"
    elif abs(mean_diff) < 0.05:
        winner = name_a if mean_diff > 0 else name_b
        confidence = "Low"
    elif abs(mean_diff) < 0.10:
        winner = name_a if mean_diff > 0 else name_b
        confidence = "Medium"
    else:
        winner = name_a if mean_diff > 0 else name_b
        confidence = "High"

    pooled_std = np.sqrt(
        (results_a.std_dev ** 2 + results_b.std_dev ** 2) / 2
    )
    if pooled_std > 0:
        effect_size = abs(mean_diff) / pooled_std
        if effect_size > 0.8:
            confidence = "High"
        elif effect_size > 0.5:
            confidence = "Medium" if confidence != "High" else "High"

    return ABTestResult(
        product_a_name=name_a,
        product_b_name=name_b,
        results_a=results_a,
        results_b=results_b,
        mean_diff=mean_diff,
        relative_diff_pct=relative_diff_pct,
        winner=winner,
        confidence=confidence,
    )


def format_ab_comparison(ab_result: ABTestResult) -> str:
    """
    Format A/B test result as human-readable text.

    Args:
        ab_result: A/B test comparison result

    Returns:
        Formatted text summary
    """
    lines = [
        "A/B Test Comparison",
        "=" * 50,
        "",
        f"Product A: {ab_result.product_a_name}",
        f"  Mean Score: {ab_result.results_a.mean_score:.2f}",
        f"  Std Dev: {ab_result.results_a.std_dev:.3f}",
        f"  Sample Size: {ab_result.results_a.sample_size}",
        "",
        f"Product B: {ab_result.product_b_name}",
        f"  Mean Score: {ab_result.results_b.mean_score:.2f}",
        f"  Std Dev: {ab_result.results_b.std_dev:.3f}",
        f"  Sample Size: {ab_result.results_b.sample_size}",
        "",
        "-" * 50,
        f"Difference: {ab_result.mean_diff:+.3f} ({ab_result.relative_diff_pct:+.1f}%)",
        f"Winner: {ab_result.winner}",
        f"Confidence: {ab_result.confidence}",
    ]
    return "\n".join(lines)


def format_summary_text(aggregated: AggregatedResults) -> str:
    """
    Format aggregated results as human-readable text.

    Args:
        aggregated: Aggregated results

    Returns:
        Formatted text summary
    """
    lines = [
        "Survey Results Summary",
        "=" * 40,
        f"Sample Size: {aggregated.sample_size}",
        f"Mean Score: {aggregated.mean_score:.2f} (scale 0-1)",
        f"Median Score: {aggregated.median_score:.2f}",
        f"Std Dev: {aggregated.std_dev:.3f}",
        f"Score Range: {aggregated.min_score:.2f} - {aggregated.max_score:.2f}",
        "",
        f"Total Cost: ${aggregated.total_cost:.4f}",
        f"Total Tokens: {aggregated.total_tokens:,}",
        f"Avg Latency: {aggregated.avg_latency_ms:.0f}ms",
    ]

    if aggregated.score_distribution:
        lines.append("")
        lines.append("Score Distribution:")
        for label, count in sorted(aggregated.score_distribution.items()):
            bar = "#" * count
            lines.append(f"  {label}: {bar} ({count})")

    return "\n".join(lines)
