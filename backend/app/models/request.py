"""Request models for API endpoints."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DemographicsFilter(BaseModel):
    """Optional demographic targeting filters."""

    age_range: Optional[tuple[int, int]] = Field(
        None,
        description="Age range as (min, max), e.g., (25, 45)",
    )
    gender: Optional[list[str]] = Field(
        None,
        description="List of genders to include",
    )
    income_bracket: Optional[list[str]] = Field(
        None,
        description="List of income brackets to include",
    )
    occupation: Optional[list[str]] = Field(
        None,
        description="List of occupations to include",
    )
    location: Optional[list[str]] = Field(
        None,
        description="List of locations to include",
    )

    @field_validator("age_range")
    @classmethod
    def validate_age_range(cls, v):
        if v is not None:
            min_age, max_age = v
            if min_age < 18 or max_age > 80:
                raise ValueError("Age range must be between 18 and 80")
            if min_age > max_age:
                raise ValueError("Min age must be less than max age")
        return v


class SurveyRequest(BaseModel):
    """Request model for running a survey."""

    product_description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Description of the product to evaluate",
    )
    sample_size: int = Field(
        20,
        ge=5,
        le=200,
        description="Number of synthetic respondents",
    )
    demographics: Optional[DemographicsFilter] = Field(
        None,
        description="Optional demographic targeting",
    )
    use_mock: bool = Field(
        False,
        description="Use mock data (no API calls)",
    )
    model: str = Field(
        "gpt-5-nano",
        description="LLM model to use",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "product_description": "A smart coffee mug that keeps your drink at the perfect temperature all day. Price: $79.",
                    "sample_size": 20,
                    "use_mock": True,
                }
            ]
        }
    }


class ABTestRequest(BaseModel):
    """Request model for A/B testing."""

    product_a: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Description of product A",
    )
    product_b: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Description of product B",
    )
    product_a_name: str = Field(
        "Product A",
        max_length=100,
        description="Display name for product A",
    )
    product_b_name: str = Field(
        "Product B",
        max_length=100,
        description="Display name for product B",
    )
    sample_size: int = Field(
        20,
        ge=5,
        le=200,
        description="Number of synthetic respondents per product",
    )
    demographics: Optional[DemographicsFilter] = Field(
        None,
        description="Optional demographic targeting",
    )
    use_mock: bool = Field(
        False,
        description="Use mock data (no API calls)",
    )
    model: str = Field(
        "gpt-5-nano",
        description="LLM model to use",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "product_a": "Smart mug with temperature control - $79",
                    "product_b": "Regular insulated mug - $15",
                    "product_a_name": "Smart Mug",
                    "product_b_name": "Regular Mug",
                    "sample_size": 30,
                    "use_mock": True,
                }
            ]
        }
    }
