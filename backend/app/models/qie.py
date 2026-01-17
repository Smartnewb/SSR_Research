"""QIE (Qualitative Insight Engine) data models.

Two-Tier Map-Reduce architecture:
- Tier 1: Data structuring with gpt-5-mini (Map Phase)
- Tier 2: Insight synthesis with gpt-5.2 (Reduce Phase)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class QIEJobStatus(str, Enum):
    """QIE job status enum."""

    PENDING = "pending"
    TIER1_PROCESSING = "tier1_processing"
    AGGREGATING = "aggregating"
    TIER2_SYNTHESIS = "tier2_synthesis"
    COMPLETED = "completed"
    FAILED = "failed"


class SentimentCategory(str, Enum):
    """Response sentiment category."""

    PRICE = "Price"
    UX = "UX"
    TRUST = "Trust"
    FEATURE = "Feature"
    CONVENIENCE = "Convenience"
    OTHER = "Other"


class KanoCategory(str, Enum):
    """Kano model feature classification."""

    MUST_BE = "Must-be"
    PERFORMANCE = "Performance"
    DELIGHTER = "Delighter"
    INDIFFERENT = "Indifferent"


class ImpactDirection(str, Enum):
    """Impact direction for key drivers."""

    POSITIVE = "positive"
    NEGATIVE = "negative"


class ActionPriority(str, Enum):
    """Action item priority level."""

    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Tier1Result:
    """Result from Tier 1 (gpt-5-mini) processing of a single response."""

    response_id: str
    sentiment: int  # 1-10 scale
    category: SentimentCategory
    keywords: list[str]
    original_text: str = ""
    ssr_score: float = 0.0


@dataclass
class CategoryStats:
    """Statistics for a single category."""

    category: str
    count: int
    percentage: float
    avg_sentiment: float
    avg_ssr: float
    top_keywords: list[str]


@dataclass
class AggregatedStats:
    """Aggregated statistics from Tier 1 results."""

    total_responses: int
    avg_sentiment: float
    sentiment_distribution: dict[int, int]  # sentiment score -> count
    category_stats: list[CategoryStats]
    keyword_frequency: dict[str, int]  # keyword -> count
    segment_breakdown: dict[str, dict]  # demographic -> stats
    low_ssr_responses: list[Tier1Result]  # SSR < 0.4
    high_ssr_responses: list[Tier1Result]  # SSR > 0.7


@dataclass
class KeyDriver:
    """Key driver affecting purchase intent."""

    factor: str
    impact: ImpactDirection
    correlation: float  # -1.0 to 1.0
    description: str
    evidence_count: int = 0
    example_quotes: list[str] = field(default_factory=list)


@dataclass
class KanoFeature:
    """Feature classified using Kano model."""

    feature_name: str
    category: KanoCategory
    satisfaction_impact: float  # -1.0 to 1.0
    mention_count: int
    description: str


@dataclass
class KanoClassification:
    """Complete Kano model classification."""

    must_be_features: list[KanoFeature]
    performance_features: list[KanoFeature]
    delighter_features: list[KanoFeature]
    indifferent_features: list[KanoFeature]


@dataclass
class SegmentInsight:
    """Insight for a specific demographic segment."""

    segment_name: str
    segment_value: str
    sample_size: int
    avg_ssr: float
    avg_sentiment: float
    top_concerns: list[str]
    key_preferences: list[str]


@dataclass
class SegmentAnalysis:
    """Cross-segment analysis results."""

    by_age: list[SegmentInsight]
    by_gender: list[SegmentInsight]
    by_income: list[SegmentInsight]
    notable_differences: list[str]


@dataclass
class PainPoint:
    """Identified pain point from responses."""

    category: SentimentCategory
    score: float  # 0-100 severity
    description: str
    affected_percentage: float
    example_quotes: list[str] = field(default_factory=list)


@dataclass
class ActionItem:
    """Recommended action item."""

    title: str
    description: str
    priority: ActionPriority
    category: str
    expected_impact: str
    related_pain_points: list[str] = field(default_factory=list)


@dataclass
class QIEAnalysis:
    """Complete QIE analysis result (Tier 2 output)."""

    executive_summary: str
    key_drivers: list[KeyDriver]
    kano_classification: KanoClassification
    segment_analysis: SegmentAnalysis
    pain_points: list[PainPoint]
    action_items: list[ActionItem]
    confidence_score: float = 0.8
    analysis_metadata: dict = field(default_factory=dict)


@dataclass
class QIEJob:
    """QIE job tracking."""

    job_id: str
    workflow_id: str
    status: QIEJobStatus
    progress: float  # 0.0 to 1.0
    current_stage: str = ""
    message: str = ""
    total_responses: int = 0
    processed_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class QIEResult:
    """Complete QIE result stored in database."""

    job_id: str
    workflow_id: str
    tier1_results: list[Tier1Result]
    aggregated_stats: AggregatedStats
    analysis: QIEAnalysis
    execution_time: float = 0.0
    tier1_time: float = 0.0
    tier2_time: float = 0.0
    created_at: Optional[datetime] = None
