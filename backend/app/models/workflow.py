"""Survey workflow models."""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from .comparison import ConceptInput


class WorkflowStatus(str, Enum):
    """Survey workflow status."""

    PRODUCT_INPUT = "product_input"
    PERSONA_BUILDING = "persona_building"
    PERSONA_CONFIRMING = "persona_confirming"
    SAMPLE_SIZE_SELECTION = "sample_size_selection"
    GENERATING_PERSONAS = "generating_personas"
    CONCEPTS_MANAGEMENT = "concepts_management"  # Step 6: Add/edit concepts
    SURVEYING = "surveying"
    COMPLETED = "completed"
    FAILED = "failed"


class ProductDescription(BaseModel):
    """Product description for survey."""

    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=2000)
    features: list[str] = Field(default_factory=list)
    price_point: Optional[str] = Field(None, max_length=100)
    target_market: str = Field(..., min_length=1, max_length=200)


class CorePersona(BaseModel):
    """Core persona definition (7 fields from paper)."""

    age_range: tuple[int, int] = Field(..., description="Min and max age")
    gender_distribution: dict[str, float] = Field(
        ..., description="Gender distribution percentages"
    )
    income_brackets: dict[str, float] = Field(
        ..., description="Income bracket distribution"
    )
    location: str = Field(..., description="Geographic location type")
    category_usage: str = Field(..., description="Product category usage level")
    shopping_behavior: str = Field(..., description="Shopping behavior pattern")
    key_pain_points: list[str] = Field(
        ..., min_length=1, description="Key pain points"
    )
    decision_drivers: list[str] = Field(
        ..., min_length=1, description="Purchase decision drivers"
    )
    currency: str = Field(default="KRW", description="Currency for income (KRW or USD)")


class ArchetypeSegment(BaseModel):
    """Single archetype segment for Multi-Archetype Stratified Sampling."""

    segment_id: Optional[str] = None
    segment_name: str
    share_ratio: float = Field(..., ge=0.0, le=1.0)
    demographics: dict = Field(default_factory=dict)
    income_level: str = "mid"
    location: str = Field(
        default="urban",
        description="Geographic location type: urban, suburban, rural, mixed"
    )
    category_usage: str = "medium"
    shopping_behavior: str = "smart_shopper"
    core_traits: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    decision_drivers: list[str] = Field(default_factory=list)


class SurveyWorkflow(BaseModel):
    """Survey workflow orchestration."""

    id: str
    product: Optional[ProductDescription] = None
    core_persona: Optional[CorePersona] = None
    archetypes: List[ArchetypeSegment] = Field(
        default_factory=list,
        description="Multi-Archetype segments (v2.0). If empty, uses single core_persona.",
    )
    use_multi_archetype: bool = Field(
        default=False,
        description="Enable Multi-Archetype Stratified Sampling mode.",
    )
    currency: str = Field(
        default="KRW",
        description="Currency for income ranges (KRW or USD).",
    )
    sample_size: Optional[int] = Field(None, ge=10, le=10000)
    concepts: List[ConceptInput] = Field(
        default_factory=list,
        description="1-5 concepts to compare. If empty, product is used as single concept.",
    )
    status: WorkflowStatus = WorkflowStatus.PRODUCT_INPUT
    current_step: int = 1
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    persona_generation_job_id: Optional[str] = None
    survey_execution_job_id: Optional[str] = None
    error_message: Optional[str] = None


class WorkflowStepRequest(BaseModel):
    """Request to progress workflow to next step."""

    step: int = Field(..., ge=1, le=7)
    data: dict = Field(default_factory=dict)


class ProductDescriptionRequest(BaseModel):
    """Request for product description."""

    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=2000)
    features: list[str] = Field(default_factory=list)
    price_point: Optional[str] = Field(None, max_length=100)
    target_market: str = Field(..., min_length=1, max_length=200)

    @field_validator("price_point", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v


class ProductDescriptionAssistRequest(BaseModel):
    """Request for AI-assisted product description."""

    product_name: str = Field(..., min_length=1, max_length=200)
    brief_description: str = Field(..., min_length=5, max_length=500)
    target_audience: Optional[str] = Field(None, max_length=200)


class CorePersonaRequest(BaseModel):
    """Request for core persona."""

    age_range: tuple[int, int]
    gender_distribution: dict[str, float]
    income_brackets: dict[str, float]
    location: str
    category_usage: str
    shopping_behavior: str
    key_pain_points: list[str]
    decision_drivers: list[str]
    currency: str = "KRW"


class SampleSizeRequest(BaseModel):
    """Request for sample size selection."""

    sample_size: int = Field(..., ge=10, le=10000)
    use_multi_archetype: bool = Field(
        default=False,
        description="Enable Multi-Archetype Stratified Sampling mode.",
    )
    archetypes: Optional[List[dict]] = Field(
        default=None,
        description="Archetype segments for Multi-Archetype mode.",
    )
    enrich: bool = Field(
        default=True,
        description="Enable LLM enrichment for persona bios.",
    )


class ConceptsRequest(BaseModel):
    """Request for concepts management (Step 6)."""

    concepts: List[ConceptInput] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="1-5 concepts to compare",
    )
