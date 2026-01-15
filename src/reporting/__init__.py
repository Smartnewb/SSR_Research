"""Reporting and aggregation module for survey results."""

from .aggregator import (
    SurveyResult,
    AggregatedResults,
    aggregate_results,
    calculate_statistics,
    calculate_distribution,
    get_top_responses,
    format_summary_text,
)

__all__ = [
    "SurveyResult",
    "AggregatedResults",
    "aggregate_results",
    "calculate_statistics",
    "calculate_distribution",
    "get_top_responses",
    "format_summary_text",
]
