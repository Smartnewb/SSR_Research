"""Product Concept Card models for API endpoints."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ConceptAssistRequest(BaseModel):
    """Request model for AI writing assistant."""

    field: str = Field(
        ...,
        description="Field to assist with: title, headline, insight, benefit, rtb, image_description, price",
    )
    rough_idea: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="User's rough idea for the field",
    )
    context: dict = Field(
        default_factory=dict,
        description="Context including product_category and target_persona",
    )

    @field_validator("field")
    @classmethod
    def validate_field(cls, v):
        allowed = ["title", "headline", "insight", "benefit", "rtb", "image_description", "price"]
        if v.lower() not in allowed:
            raise ValueError(f"Field must be one of: {allowed}")
        return v.lower()


class SuggestionItem(BaseModel):
    """A single AI suggestion."""

    text: str = Field(..., description="Suggested text")
    rationale: str = Field(..., description="Explanation for the suggestion")


class ConceptAssistResponse(BaseModel):
    """Response model for AI writing assistant."""

    suggestions: list[SuggestionItem] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="List of AI suggestions",
    )


class ProductConcept(BaseModel):
    """Product concept card with 7 required fields."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Product name",
    )
    headline: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="One-sentence hook",
    )
    consumer_insight: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Consumer pain point as a relatable statement",
    )
    benefit: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Core benefit/solution",
    )
    rtb: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason to Believe - technical credibility",
    )
    image_description: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Product appearance description",
    )
    price: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Price with context (size, promo)",
    )


class ConceptValidateRequest(ProductConcept):
    """Request model for concept validation."""
    pass


class FieldFeedback(BaseModel):
    """Feedback for a single field."""

    status: str = Field(..., description="good, warning, or excellent")
    message: str = Field(..., description="Feedback message")


class ConceptValidateResponse(BaseModel):
    """Response model for concept validation."""

    is_valid: bool = Field(..., description="Whether the concept passes validation")
    score: int = Field(..., ge=0, le=100, description="Overall score 0-100")
    feedback: dict[str, FieldFeedback] = Field(
        ...,
        description="Feedback for each field",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Improvement suggestions",
    )


class SaveConceptRequest(ProductConcept):
    """Request model for saving a concept."""

    persona_id: Optional[str] = Field(
        None,
        description="Associated persona ID",
    )


class SaveConceptResponse(BaseModel):
    """Response model for saved concept."""

    id: str = Field(..., description="Unique concept ID")
    validation_score: int = Field(..., description="Validation score")
    created_at: str = Field(..., description="Creation timestamp")
