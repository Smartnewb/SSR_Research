"""Results aggregation and statistical analysis."""

import re
from collections import Counter
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


STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of",
    "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just",
    "don", "should", "now", "would", "could", "might", "must", "shall", "may",
    "product", "buy", "purchase", "would", "think", "like", "really", "also",
}


@dataclass
class KeywordInsight:
    """Keyword analysis insight for qualitative data."""

    keyword: str
    frequency: int
    tf_idf_score: float
    sentiment_context: str  # "positive", "negative", "neutral"
    avg_score_when_present: float


@dataclass
class QualitativeInsights:
    """Qualitative analysis results from response texts."""

    top_keywords: list[KeywordInsight]
    positive_keywords: list[KeywordInsight]
    negative_keywords: list[KeywordInsight]
    total_responses: int
    avg_response_length: float
    insight_summary: str


def extract_keywords(
    texts: list[str],
    top_n: int = 20,
    min_word_length: int = 3,
) -> list[tuple[str, int]]:
    """
    Extract keywords from texts using frequency analysis.

    Args:
        texts: List of response texts
        top_n: Number of top keywords to return
        min_word_length: Minimum word length to consider

    Returns:
        List of (keyword, frequency) tuples
    """
    word_counts: Counter = Counter()

    for text in texts:
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        filtered = [
            w for w in words
            if len(w) >= min_word_length and w not in STOP_WORDS
        ]
        word_counts.update(filtered)

    return word_counts.most_common(top_n)


def calculate_tf_idf(
    texts: list[str],
    top_n: int = 20,
    min_word_length: int = 3,
) -> list[tuple[str, float]]:
    """
    Calculate TF-IDF scores for keywords.

    Args:
        texts: List of response texts
        top_n: Number of top keywords to return
        min_word_length: Minimum word length to consider

    Returns:
        List of (keyword, tf_idf_score) tuples
    """
    if not texts:
        return []

    doc_freq: Counter = Counter()
    term_freq: Counter = Counter()

    for text in texts:
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        filtered = [
            w for w in words
            if len(w) >= min_word_length and w not in STOP_WORDS
        ]
        term_freq.update(filtered)
        doc_freq.update(set(filtered))

    n_docs = len(texts)
    tf_idf_scores = {}

    for word, tf in term_freq.items():
        df = doc_freq[word]
        idf = np.log(n_docs / (df + 1)) + 1
        tf_idf_scores[word] = tf * idf

    sorted_scores = sorted(tf_idf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_scores[:top_n]


def analyze_qualitative_data(
    results: list[SurveyResult],
    score_threshold_positive: float = 0.6,
    score_threshold_negative: float = 0.4,
    top_n: int = 10,
) -> QualitativeInsights:
    """
    Analyze qualitative data from survey responses.

    Extracts keywords and provides insights based on response texts,
    correlating with SSR scores.

    Args:
        results: List of survey results with response texts
        score_threshold_positive: Score above this is considered positive
        score_threshold_negative: Score below this is considered negative
        top_n: Number of top keywords per category

    Returns:
        QualitativeInsights with keyword analysis
    """
    if not results:
        return QualitativeInsights(
            top_keywords=[],
            positive_keywords=[],
            negative_keywords=[],
            total_responses=0,
            avg_response_length=0.0,
            insight_summary="No responses to analyze.",
        )

    all_texts = [r.response_text for r in results]
    positive_texts = [r.response_text for r in results if r.ssr_score >= score_threshold_positive]
    negative_texts = [r.response_text for r in results if r.ssr_score <= score_threshold_negative]

    tf_idf_all = calculate_tf_idf(all_texts, top_n)
    tf_idf_positive = calculate_tf_idf(positive_texts, top_n)
    tf_idf_negative = calculate_tf_idf(negative_texts, top_n)

    def build_insights(
        tf_idf_list: list[tuple[str, float]],
        results: list[SurveyResult],
        sentiment: str,
    ) -> list[KeywordInsight]:
        insights = []
        for keyword, score in tf_idf_list:
            matching = [
                r for r in results
                if keyword in r.response_text.lower()
            ]
            frequency = len(matching)
            avg_score = (
                sum(r.ssr_score for r in matching) / frequency
                if frequency > 0 else 0.0
            )
            insights.append(KeywordInsight(
                keyword=keyword,
                frequency=frequency,
                tf_idf_score=score,
                sentiment_context=sentiment,
                avg_score_when_present=avg_score,
            ))
        return insights

    top_keywords = build_insights(tf_idf_all, results, "neutral")
    positive_keywords = build_insights(tf_idf_positive, results, "positive")
    negative_keywords = build_insights(tf_idf_negative, results, "negative")

    avg_length = sum(len(t.split()) for t in all_texts) / len(all_texts) if all_texts else 0

    pos_key_str = ", ".join(k.keyword for k in positive_keywords[:3]) if positive_keywords else "none"
    neg_key_str = ", ".join(k.keyword for k in negative_keywords[:3]) if negative_keywords else "none"
    avg_score = sum(r.ssr_score for r in results) / len(results)

    insight_summary = (
        f"Analysis of {len(results)} responses (avg score: {avg_score:.2f}). "
        f"Positive responses frequently mention: {pos_key_str}. "
        f"Negative responses frequently mention: {neg_key_str}."
    )

    return QualitativeInsights(
        top_keywords=top_keywords,
        positive_keywords=positive_keywords,
        negative_keywords=negative_keywords,
        total_responses=len(results),
        avg_response_length=avg_length,
        insight_summary=insight_summary,
    )


def format_qualitative_insights(insights: QualitativeInsights) -> str:
    """
    Format qualitative insights as human-readable text.

    Args:
        insights: Qualitative analysis results

    Returns:
        Formatted text summary
    """
    lines = [
        "Qualitative Analysis",
        "=" * 50,
        "",
        f"Total Responses: {insights.total_responses}",
        f"Avg Response Length: {insights.avg_response_length:.1f} words",
        "",
        insights.insight_summary,
        "",
        "-" * 50,
        "Top Keywords (Overall):",
    ]

    for kw in insights.top_keywords[:5]:
        lines.append(
            f"  {kw.keyword}: freq={kw.frequency}, "
            f"avg_score={kw.avg_score_when_present:.2f}"
        )

    if insights.positive_keywords:
        lines.append("")
        lines.append("Keywords in Positive Responses (score >= 0.6):")
        for kw in insights.positive_keywords[:5]:
            lines.append(f"  {kw.keyword}: freq={kw.frequency}")

    if insights.negative_keywords:
        lines.append("")
        lines.append("Keywords in Negative Responses (score <= 0.4):")
        for kw in insights.negative_keywords[:5]:
            lines.append(f"  {kw.keyword}: freq={kw.frequency}")

    return "\n".join(lines)
