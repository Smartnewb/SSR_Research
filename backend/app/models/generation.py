"""Persona generation models for API endpoints."""

from typing import Optional
from pydantic import BaseModel, Field


class GeneratePersonasRequest(BaseModel):
    """Request model for generating synthetic personas."""

    core_persona_id: str = Field(
        ...,
        description="ID of the core persona to base generation on",
    )
    sample_size: int = Field(
        100,
        ge=10,
        le=10000,
        description="Number of personas to generate (10-10,000)",
    )
    random_seed: Optional[int] = Field(
        None,
        description="Random seed for reproducibility",
    )


class GeneratePersonasResponse(BaseModel):
    """Initial response for persona generation job."""

    job_id: str = Field(..., description="Unique job ID")
    status: str = Field(..., description="Job status")
    estimated_time_seconds: int = Field(..., description="Estimated time in seconds")
    websocket_url: str = Field(..., description="WebSocket URL for progress")


class GenerationSummary(BaseModel):
    """Summary statistics for generated personas."""

    total_personas: int
    distribution_stats: dict


class GenerationCompleteResponse(BaseModel):
    """Final response when generation is complete."""

    job_id: str
    download_url: str
    summary: GenerationSummary


class PreviewPersona(BaseModel):
    """Preview persona for display."""

    id: str
    age: int
    gender: str
    income_bracket: str
    system_prompt: str


class PreviewPersonasResponse(BaseModel):
    """Response model for persona preview."""

    preview_personas: list[PreviewPersona]
