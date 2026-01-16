"""Persona generation API routes for workflow."""

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..services.persona_generation import (
    generate_synthetic_sample,
    calculate_distribution_stats,
)
from ..services.workflow import get_workflow_service
from ..services import database as db

router = APIRouter(prefix="/api/workflows/{workflow_id}/generate", tags=["generation"])


class GenerationStatus(BaseModel):
    """Status of persona generation."""

    job_id: str
    workflow_id: str
    status: str
    total_personas: int
    generated_count: int
    progress: float
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None


class GenerationResult(BaseModel):
    """Result of persona generation."""

    job_id: str
    workflow_id: str
    total_personas: int
    distribution_stats: dict
    personas: list[dict]


# In-memory cache for active jobs
_generation_jobs: dict[str, GenerationStatus] = {}
_generation_results: dict[str, GenerationResult] = {}


def _save_job_to_db(status: GenerationStatus):
    """Save job status to database."""
    db.save_generation_job(
        job_id=status.job_id,
        workflow_id=status.workflow_id,
        status=status.status,
        total_personas=status.total_personas,
        generated_count=status.generated_count,
        progress=status.progress,
        started_at=status.started_at,
        completed_at=status.completed_at,
        error=status.error,
    )


def _load_job_from_db(job_id: str) -> GenerationStatus | None:
    """Load job status from database."""
    data = db.load_generation_job(job_id)
    if not data:
        return None
    return GenerationStatus(**data)


def _save_result_to_db(result: GenerationResult):
    """Save result to database."""
    db.save_generation_result(
        job_id=result.job_id,
        workflow_id=result.workflow_id,
        total_personas=result.total_personas,
        distribution_stats=result.distribution_stats,
        personas=result.personas,
    )


def _load_result_from_db(job_id: str) -> GenerationResult | None:
    """Load result from database."""
    data = db.load_generation_result(job_id)
    if not data:
        return None
    return GenerationResult(**data)


async def _generate_personas_background(
    job_id: str, workflow_id: str, core_persona: dict, sample_size: int
):
    """Background task for generating personas."""
    try:
        _generation_jobs[job_id].status = "generating"
        _save_job_to_db(_generation_jobs[job_id])

        await asyncio.sleep(0.5)

        personas = generate_synthetic_sample(core_persona, sample_size)

        _generation_jobs[job_id].generated_count = len(personas)
        _generation_jobs[job_id].progress = 1.0
        _generation_jobs[job_id].status = "completed"
        _generation_jobs[job_id].completed_at = datetime.now(timezone.utc)
        _save_job_to_db(_generation_jobs[job_id])

        stats = calculate_distribution_stats(personas)

        result = GenerationResult(
            job_id=job_id,
            workflow_id=workflow_id,
            total_personas=len(personas),
            distribution_stats=stats,
            personas=personas,
        )
        _generation_results[job_id] = result
        _save_result_to_db(result)

    except Exception as e:
        _generation_jobs[job_id].status = "failed"
        _generation_jobs[job_id].error = str(e)
        _save_job_to_db(_generation_jobs[job_id])

        workflow_service = get_workflow_service()
        workflow_service.fail_workflow(workflow_id, f"Persona generation failed: {e}")


@router.post("/start", response_model=GenerationStatus)
async def start_generation(workflow_id: str, background_tasks: BackgroundTasks):
    """Start persona generation (Step 5).

    This triggers background generation of N persona variations
    based on the core persona and sample size.
    """
    workflow_service = get_workflow_service()
    workflow = workflow_service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not workflow.core_persona:
        raise HTTPException(status_code=400, detail="Core persona not set")

    if not workflow.sample_size:
        raise HTTPException(status_code=400, detail="Sample size not set")

    job_id = f"GEN_{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    status = GenerationStatus(
        job_id=job_id,
        workflow_id=workflow_id,
        status="queued",
        total_personas=workflow.sample_size,
        generated_count=0,
        progress=0.0,
        started_at=now,
    )

    _generation_jobs[job_id] = status
    _save_job_to_db(status)

    workflow_service.start_persona_generation(workflow_id, job_id)

    core_persona_dict = workflow.core_persona.model_dump()
    background_tasks.add_task(
        _generate_personas_background,
        job_id,
        workflow_id,
        core_persona_dict,
        workflow.sample_size,
    )

    return status


@router.get("/status", response_model=GenerationStatus)
async def get_generation_status(workflow_id: str):
    """Get persona generation status.

    Check the progress of persona generation.
    """
    workflow_service = get_workflow_service()
    workflow = workflow_service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not workflow.persona_generation_job_id:
        raise HTTPException(status_code=404, detail="No generation job found")

    job_id = workflow.persona_generation_job_id

    # Try memory cache first
    status = _generation_jobs.get(job_id)

    # Try database if not in memory
    if not status:
        status = _load_job_from_db(job_id)
        if status:
            _generation_jobs[job_id] = status

    if not status:
        raise HTTPException(status_code=404, detail="Generation job not found")

    return status


@router.get("/result", response_model=GenerationResult)
async def get_generation_result(workflow_id: str):
    """Get persona generation result.

    Returns the generated personas and distribution stats.
    Only available after generation is completed.
    """
    workflow_service = get_workflow_service()
    workflow = workflow_service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not workflow.persona_generation_job_id:
        raise HTTPException(status_code=404, detail="No generation job found")

    job_id = workflow.persona_generation_job_id

    # Try memory cache first
    result = _generation_results.get(job_id)

    # Try database if not in memory
    if not result:
        result = _load_result_from_db(job_id)
        if result:
            _generation_results[job_id] = result

    if not result:
        # Check job status
        status = _generation_jobs.get(job_id) or _load_job_from_db(job_id)
        if status and status.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Generation not completed. Status: {status.status}",
            )
        raise HTTPException(status_code=404, detail="Generation result not found")

    return result
