"""Research and Persona models for API endpoints."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ResearchPromptRequest(BaseModel):
    """Request model for generating research prompts."""

    product_category: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Product category (e.g., 'oral care', 'skincare')",
    )
    target_description: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Description of target audience",
    )
    market: str = Field(
        "korea",
        description="Target market: korea, us, global",
    )

    @field_validator("market")
    @classmethod
    def validate_market(cls, v):
        allowed = ["korea", "us", "global", "japan", "china", "europe"]
        if v.lower() not in allowed:
            raise ValueError(f"Market must be one of: {allowed}")
        return v.lower()


class ResearchPromptResponse(BaseModel):
    """Response model for research prompt generation."""

    research_prompt: str = Field(
        ...,
        description="Generated prompt for Gemini Deep Research",
    )
    instructions: str = Field(
        ...,
        description="User instructions in Korean",
    )


class GenderDistribution(BaseModel):
    """Gender distribution percentages."""

    female: int = Field(50, ge=0, le=100)
    male: int = Field(50, ge=0, le=100)

    @field_validator("male")
    @classmethod
    def validate_total(cls, v, info):
        female = info.data.get("female", 50)
        if female + v != 100:
            raise ValueError("Gender distribution must sum to 100")
        return v


class IncomeBrackets(BaseModel):
    """Income distribution percentages."""

    low: int = Field(30, ge=0, le=100)
    mid: int = Field(50, ge=0, le=100)
    high: int = Field(20, ge=0, le=100)

    @field_validator("high")
    @classmethod
    def validate_total(cls, v, info):
        low = info.data.get("low", 30)
        mid = info.data.get("mid", 50)
        if low + mid + v != 100:
            raise ValueError("Income brackets must sum to 100")
        return v


class CorePersona(BaseModel):
    """Core persona profile extracted from research."""

    age_range: tuple[int, int] = Field(
        ...,
        description="Age range as [min, max]",
    )
    gender_distribution: GenderDistribution = Field(
        default_factory=GenderDistribution,
        description="Gender distribution percentages",
    )
    income_brackets: IncomeBrackets = Field(
        default_factory=IncomeBrackets,
        description="Income bracket distribution",
    )
    location: str = Field(
        "urban",
        description="Location type: urban, suburban, rural, mixed",
    )
    category_usage: str = Field(
        "medium",
        description="Product usage frequency: high, medium, low",
    )
    shopping_behavior: str = Field(
        "smart_shopper",
        description="Shopping behavior type",
    )
    key_pain_points: list[str] = Field(
        default_factory=list,
        min_length=1,
        max_length=10,
        description="Key pain points (2-5 items)",
    )
    decision_drivers: list[str] = Field(
        default_factory=list,
        min_length=1,
        max_length=10,
        description="Purchase decision drivers",
    )

    @field_validator("age_range")
    @classmethod
    def validate_age_range(cls, v):
        min_age, max_age = v
        if min_age < 15 or max_age > 80:
            raise ValueError("Age range must be between 15 and 80")
        if min_age > max_age:
            raise ValueError("Min age must be less than max age")
        return v

    @field_validator("location")
    @classmethod
    def validate_location(cls, v):
        allowed = ["urban", "suburban", "rural", "mixed"]
        if v.lower() not in allowed:
            raise ValueError(f"Location must be one of: {allowed}")
        return v.lower()

    @field_validator("category_usage")
    @classmethod
    def validate_usage(cls, v):
        allowed = ["high", "medium", "low"]
        if v.lower() not in allowed:
            raise ValueError(f"Category usage must be one of: {allowed}")
        return v.lower()


class ParseReportRequest(BaseModel):
    """Request model for parsing research reports."""

    research_report: str = Field(
        ...,
        min_length=100,
        max_length=50000,
        description="Gemini Deep Research report content",
    )


class ParseReportResponse(BaseModel):
    """Response model for parsed research report."""

    core_persona: CorePersona = Field(
        ...,
        description="Extracted persona profile",
    )
    confidence: float = Field(
        0.85,
        ge=0,
        le=1,
        description="AI confidence in extraction",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings about missing or inferred data",
    )


class SaveCorePersonaRequest(BaseModel):
    """Request model for saving core persona."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Persona profile name",
    )
    age_range: tuple[int, int]
    gender_distribution: GenderDistribution
    income_brackets: IncomeBrackets
    location: str
    category_usage: str
    shopping_behavior: str
    key_pain_points: list[str]
    decision_drivers: list[str]

    @field_validator("age_range")
    @classmethod
    def validate_age_range(cls, v):
        min_age, max_age = v
        if min_age < 15 or max_age > 80:
            raise ValueError("Age range must be between 15 and 80")
        if min_age > max_age:
            raise ValueError("Min age must be less than max age")
        return v


class SaveCorePersonaResponse(BaseModel):
    """Response model for saved core persona."""

    id: str = Field(..., description="Unique persona ID")
    created_at: str = Field(..., description="Creation timestamp")
    status: str = Field("ready_for_generation", description="Persona status")


# =============================================================================
# Multi-Archetype Stratified Sampling Pipeline (v2.0)
# =============================================================================


class ArchetypeDemographics(BaseModel):
    """Demographics for an archetype segment."""

    age_range: tuple[int, int] = Field(
        (20, 30),
        description="Age range as [min, max]",
    )
    gender_distribution: GenderDistribution = Field(
        default_factory=GenderDistribution,
        description="Gender distribution percentages",
    )

    @field_validator("age_range")
    @classmethod
    def validate_age_range(cls, v):
        min_age, max_age = v
        if min_age < 15 or max_age > 80:
            raise ValueError("Age range must be between 15 and 80")
        if min_age > max_age:
            raise ValueError("Min age must be less than max age")
        return v


class Archetype(BaseModel):
    """Single market segment archetype."""

    segment_id: Optional[str] = Field(None, description="Unique segment ID")
    segment_name: str = Field(..., min_length=2, max_length=100)
    share_ratio: float = Field(..., ge=0.0, le=1.0, description="Market share ratio (0.0-1.0)")
    demographics: ArchetypeDemographics = Field(default_factory=ArchetypeDemographics)
    income_level: str = Field("mid", description="Income level: none, low, mid, high")
    category_usage: str = Field("medium", description="Usage: high, medium, low")
    shopping_behavior: str = Field("smart_shopper", description="Shopping behavior type")
    core_traits: list[str] = Field(default_factory=list, description="Core personality traits")
    pain_points: list[str] = Field(default_factory=list, description="Key pain points")
    decision_drivers: list[str] = Field(default_factory=list, description="Decision drivers")

    @field_validator("income_level")
    @classmethod
    def validate_income_level(cls, v):
        allowed = ["none", "low", "mid", "high"]
        if v.lower() not in allowed:
            raise ValueError(f"Income level must be one of: {allowed}")
        return v.lower()

    @field_validator("category_usage")
    @classmethod
    def validate_usage(cls, v):
        allowed = ["high", "medium", "low"]
        if v.lower() not in allowed:
            raise ValueError(f"Category usage must be one of: {allowed}")
        return v.lower()


class SegmentMarketRequest(BaseModel):
    """Request model for Step 1: Market Segmentation."""

    research_report: str = Field(
        ...,
        min_length=100,
        max_length=100000,
        description="Gemini Deep Research report content",
    )
    product_category: Optional[str] = Field(
        None,
        max_length=100,
        description="Product/service category for context",
    )
    target_segments: int = Field(
        4,
        ge=3,
        le=5,
        description="Target number of segments (3-5)",
    )


class SegmentMarketResponse(BaseModel):
    """Response model for Step 1: Market Segmentation."""

    archetypes: list[Archetype] = Field(..., description="List of market segments")
    total_share: float = Field(1.0, description="Total share ratio (should be 1.0)")
    segment_count: int = Field(..., description="Number of segments")
    warnings: list[str] = Field(default_factory=list, description="Processing warnings")


class GeneratePersonasRequest(BaseModel):
    """Request model for Steps 2+3: Distribution + Enrichment."""

    archetypes: list[Archetype] = Field(..., min_length=1, description="Archetypes from Step 1")
    total_samples: int = Field(
        1000,
        ge=10,
        le=10000,
        description="Total personas to generate (10-10000)",
    )
    product_context: Optional[str] = Field(
        None,
        max_length=200,
        description="Product/service context for enrichment",
    )
    currency: str = Field("KRW", description="Currency: KRW or USD")
    enrich: bool = Field(True, description="Enable LLM enrichment (Step 3)")
    random_seed: Optional[int] = Field(None, description="Random seed for reproducibility")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        allowed = ["KRW", "USD"]
        if v.upper() not in allowed:
            raise ValueError(f"Currency must be one of: {allowed}")
        return v.upper()


class DistributionPlanItem(BaseModel):
    """Single item in distribution plan."""

    segment_id: str
    segment_name: str
    count: int = Field(..., ge=0)
    share_ratio: float = Field(..., ge=0.0, le=1.0)
    actual_ratio: float = Field(..., ge=0.0, le=1.0)


class GeneratedPersona(BaseModel):
    """Single generated persona."""

    id: str
    segment_id: Optional[str] = None
    segment_name: Optional[str] = None
    age: int
    gender: str
    income_bracket: str
    income_value: int
    currency: str
    location: str
    category_usage: str
    shopping_behavior: str
    core_traits: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    decision_drivers: list[str] = Field(default_factory=list)
    bio: Optional[str] = None
    enriched: bool = False


class DistributionStats(BaseModel):
    """Statistics for generated personas."""

    age: dict = Field(default_factory=dict)
    gender: dict = Field(default_factory=dict)
    income: dict = Field(default_factory=dict)


class GeneratePersonasResponse(BaseModel):
    """Response model for persona generation."""

    personas: list[GeneratedPersona] = Field(..., description="Generated personas")
    distribution_plan: list[DistributionPlanItem] = Field(..., description="Distribution plan")
    stats: DistributionStats = Field(..., description="Distribution statistics")
    segment_stats: dict = Field(default_factory=dict, description="Per-segment counts")
    total_count: int = Field(..., description="Total generated personas")
    enriched: bool = Field(..., description="Whether enrichment was applied")
