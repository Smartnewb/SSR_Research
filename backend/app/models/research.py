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
