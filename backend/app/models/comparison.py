"""Multi-concept comparison models."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ConceptInput(BaseModel):
    """Single concept for comparison (Concept Board format).

    Follows standard marketing research concept testing structure:
    1. Headline: Eye-catching one-liner
    2. Consumer Insight: Pain point/need (empathy)
    3. Benefits: Value propositions (list)
    4. RTB: Reasons to Believe (list)
    5. Image Prompt: Visual representation description
    """

    id: str = Field(..., description="Unique concept identifier")
    title: str = Field(..., min_length=1, max_length=100, description="Product name")
    headline: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Eye-catching one-liner (e.g., '3일 만에 2단계 더 밝은 미소')",
    )
    consumer_insight: str = Field(
        ...,
        min_length=10,
        description="Consumer pain point starting with empathy (e.g., '커피로 누렇게 변한 치아 때문에...')",
    )
    benefits: List[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="3-5 value propositions focusing on benefits, not features",
    )
    rtb: List[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Reasons to Believe - technical proof, certifications, data",
    )
    image_prompt: str = Field(
        ...,
        min_length=10,
        description="Detailed prompt for image generation (DALL-E style)",
    )
    price: str = Field(..., min_length=1, max_length=100, description="Price with unit")


class MultiCompareRequest(BaseModel):
    """Request for multi-concept comparison."""

    concepts: List[ConceptInput] = Field(
        ..., min_length=2, max_length=5, description="2-5 concepts to compare"
    )
    persona_set_id: str = Field(
        ..., description="ID of saved persona set to use for comparison"
    )
    sample_size: int = Field(
        default=500,
        ge=100,
        le=10000,
        description="Number of personas to sample from the set",
    )
    comparison_mode: Literal["rank_based", "absolute"] = Field(
        default="rank_based",
        description="rank_based: pairwise preference, absolute: independent scores",
    )
    use_mock: bool = Field(
        default=False, description="Use mock LLM responses for testing"
    )


class DistributionStats(BaseModel):
    """SSR score distribution statistics."""

    definitely_buy: float = Field(..., ge=0, le=1, description="0.8-1.0 range")
    probably_buy: float = Field(..., ge=0, le=1, description="0.6-0.8 range")
    maybe: float = Field(..., ge=0, le=1, description="0.4-0.6 range")
    unlikely: float = Field(..., ge=0, le=1, description="0.0-0.4 range")


class AbsoluteScore(BaseModel):
    """Absolute SSR score for a concept."""

    concept_id: str
    concept_title: str
    mean_ssr: float = Field(..., ge=0, le=1)
    std_dev: float = Field(..., ge=0)
    median_ssr: float = Field(..., ge=0, le=1)
    distribution: DistributionStats


class PreferenceMatrixEntry(BaseModel):
    """Single entry in pairwise preference matrix."""

    concept_a: str
    concept_b: str
    preference_rate: float = Field(
        ..., ge=0, le=1, description="% of personas that prefer A over B"
    )


class RelativePreference(BaseModel):
    """Relative preference between concepts."""

    winner: str = Field(..., description="Concept ID with highest win rate")
    preference_matrix: List[PreferenceMatrixEntry]


class StatisticalSignificance(BaseModel):
    """Statistical test results."""

    test_type: Literal["t_test", "anova"] = Field(
        ..., description="t_test for 2 concepts, anova for 3+"
    )
    statistic: float = Field(..., description="t-statistic or F-statistic")
    p_value: float = Field(..., ge=0, le=1)
    is_significant: bool = Field(..., description="p < 0.05")
    confidence_level: float = Field(default=0.95, description="Typically 0.95")
    interpretation: str = Field(
        ...,
        description="Human-readable interpretation (e.g., 'Concept A significantly outperforms B')",
    )


class SegmentAnalysis(BaseModel):
    """Winner by demographic segment."""

    segment: str = Field(..., description="e.g., 'age_30_40', 'high_income'")
    segment_size: int = Field(..., ge=1, description="Number of personas in segment")
    winner: str = Field(..., description="Concept ID that won in this segment")
    winner_mean_ssr: float = Field(..., ge=0, le=1)
    runner_up: str = Field(..., description="Second-place concept ID")
    runner_up_mean_ssr: float = Field(..., ge=0, le=1)
    mean_diff: float = Field(
        ..., description="Difference between winner and runner-up"
    )


class ComparisonResults(BaseModel):
    """Complete multi-concept comparison results."""

    absolute_scores: List[AbsoluteScore]
    relative_preference: Optional[RelativePreference] = Field(
        None, description="Only present if comparison_mode=rank_based"
    )
    statistical_significance: StatisticalSignificance
    segment_analysis: List[SegmentAnalysis]
    key_differentiators: List[str] = Field(
        ..., max_length=5, description="LLM-extracted key differentiators"
    )


class MultiCompareResponse(BaseModel):
    """Response for multi-concept comparison."""

    comparison_id: str
    results: ComparisonResults
    execution_time_ms: int = Field(..., ge=0, description="Total execution time")
    total_cost_usd: float = Field(..., ge=0, description="Estimated API cost")
    personas_tested: int = Field(..., ge=1, description="Actual number of personas used")
