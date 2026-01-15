"""Response models for API endpoints."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SurveyStatusEnum(str, Enum):
    """Survey execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SurveyResultItem(BaseModel):
    """Individual survey response result."""

    persona_id: str
    ssr_score: float = Field(..., ge=0, le=1)
    likert_5: float = Field(..., ge=1, le=5)
    scale_10: float = Field(..., ge=1, le=10)
    response_text: str
    persona_data: Optional[dict] = None
    tokens_used: int = 0
    cost: float = 0.0
    latency_ms: int = 0


class SurveyStatus(BaseModel):
    """Survey status for progress tracking."""

    survey_id: str
    status: SurveyStatusEnum
    progress: float = Field(..., ge=0, le=100)
    current_persona: Optional[int] = None
    total_personas: int
    estimated_time_remaining_seconds: Optional[float] = None
    error_message: Optional[str] = None


class SurveyResponse(BaseModel):
    """Response model for survey results."""

    survey_id: str
    product_description: str
    sample_size: int
    mean_score: float
    median_score: float
    std_dev: float
    min_score: float
    max_score: float
    score_distribution: dict[str, int]
    total_cost: float
    total_tokens: int
    execution_time_seconds: float
    results: list[SurveyResultItem]
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "survey_id": "survey_abc123",
                    "product_description": "Smart coffee mug...",
                    "sample_size": 20,
                    "mean_score": 0.65,
                    "median_score": 0.67,
                    "std_dev": 0.12,
                    "min_score": 0.35,
                    "max_score": 0.89,
                    "score_distribution": {
                        "0.0-0.1": 0,
                        "0.1-0.2": 0,
                        "0.2-0.3": 1,
                        "0.3-0.4": 2,
                        "0.4-0.5": 3,
                        "0.5-0.6": 4,
                        "0.6-0.7": 5,
                        "0.7-0.8": 3,
                        "0.8-0.9": 2,
                        "0.9-1.0": 0,
                    },
                    "total_cost": 0.05,
                    "total_tokens": 2500,
                    "execution_time_seconds": 15.3,
                    "results": [],
                }
            ]
        }
    }


class ABTestStatistics(BaseModel):
    """Statistical analysis results for A/B testing."""

    mean_difference: float
    relative_difference: float
    t_statistic: float
    p_value: float
    confidence_interval: tuple[float, float]
    effect_size: float
    significant: bool
    winner: Optional[str] = None


class ABTestResponse(BaseModel):
    """Response model for A/B test results."""

    test_id: str
    product_a_name: str
    product_b_name: str
    results_a: SurveyResponse
    results_b: SurveyResponse
    statistics: ABTestStatistics
    created_at: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    code: str
    message: str
    details: Optional[dict] = None
