"""QIE (Qualitative Insight Engine) API routes.

Provides endpoints for:
- Starting QIE analysis
- Checking analysis status
- Retrieving analysis results
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from ..models.qie import QIEJobStatus
from ..services.database import (
    load_execution_result,
    load_qie_job_by_workflow,
    load_qie_result_by_workflow,
    load_workflow,
    save_qie_job,
    save_qie_result,
    update_qie_job_progress,
)
from ..services.qie_pipeline import (
    QIEPipeline,
    aggregated_stats_to_dict,
    qie_analysis_to_dict,
    tier1_result_to_dict,
)

router = APIRouter(prefix="/api/workflows", tags=["qie"])

# In-memory job status tracking for WebSocket updates
# Stores job_id -> {job_data, created_at}
_qie_jobs: dict[str, dict] = {}

# TTL for completed jobs in memory (10 minutes)
_QIE_JOB_TTL_SECONDS = 600


def _cleanup_old_jobs():
    """Remove completed/failed jobs older than TTL from memory."""
    now = datetime.now()
    jobs_to_remove = []

    for job_id, job_data in _qie_jobs.items():
        created_at = job_data.get("_created_at")
        status = job_data.get("status")

        if status in [QIEJobStatus.COMPLETED.value, QIEJobStatus.FAILED.value]:
            if created_at and (now - created_at).total_seconds() > _QIE_JOB_TTL_SECONDS:
                jobs_to_remove.append(job_id)

    for job_id in jobs_to_remove:
        del _qie_jobs[job_id]


class QIEJobResponse(BaseModel):
    """QIE job status response."""

    job_id: str
    workflow_id: str
    status: str
    progress: float
    current_stage: str
    message: str
    total_responses: int
    processed_count: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class QIEResultResponse(BaseModel):
    """QIE analysis result response."""

    job_id: str
    workflow_id: str
    analysis: dict
    aggregated_stats: dict
    execution_time: float
    tier1_time: float
    tier2_time: float


@router.post("/{workflow_id}/qie/start", response_model=QIEJobResponse)
async def start_qie_analysis(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    force: bool = False,
):
    """Start QIE analysis for a workflow.

    Args:
        workflow_id: The workflow ID
        force: If True, restart analysis even if one exists
    """
    # Check workflow exists
    workflow = load_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Check if analysis already running
    existing_job = load_qie_job_by_workflow(workflow_id)
    if existing_job and not force:
        if existing_job["status"] in [
            QIEJobStatus.PENDING.value,
            QIEJobStatus.TIER1_PROCESSING.value,
            QIEJobStatus.AGGREGATING.value,
            QIEJobStatus.TIER2_SYNTHESIS.value,
        ]:
            raise HTTPException(
                status_code=409,
                detail="QIE analysis already in progress",
            )

        if existing_job["status"] == QIEJobStatus.COMPLETED.value:
            # Return existing completed job
            return QIEJobResponse(
                job_id=existing_job["job_id"],
                workflow_id=workflow_id,
                status=existing_job["status"],
                progress=existing_job["progress"],
                current_stage=existing_job["current_stage"] or "",
                message=existing_job["message"] or "분석 완료",
                total_responses=existing_job["total_responses"],
                processed_count=existing_job["processed_count"],
                started_at=existing_job["started_at"].isoformat() if existing_job["started_at"] else None,
                completed_at=existing_job["completed_at"].isoformat() if existing_job["completed_at"] else None,
            )

    # Get execution results to analyze
    if not workflow.survey_execution_job_id:
        raise HTTPException(
            status_code=400,
            detail="Survey not executed yet. Run survey first.",
        )

    execution_result = load_execution_result(workflow.survey_execution_job_id)
    if not execution_result:
        raise HTTPException(
            status_code=400,
            detail="Execution results not found. Run survey first.",
        )

    responses = execution_result.get("results", [])
    if not responses:
        raise HTTPException(
            status_code=400,
            detail="No survey responses to analyze",
        )

    # Create new job
    job_id = f"qie_{uuid.uuid4().hex[:12]}"
    started_at = datetime.now()

    # Save initial job status
    save_qie_job(
        job_id=job_id,
        workflow_id=workflow_id,
        status=QIEJobStatus.PENDING.value,
        progress=0.0,
        total_responses=len(responses),
        processed_count=0,
        started_at=started_at,
        current_stage="pending",
        message="분석 시작 대기 중...",
    )

    # Cleanup old completed jobs before adding new one
    _cleanup_old_jobs()

    # Track in memory for WebSocket updates
    _qie_jobs[job_id] = {
        "job_id": job_id,
        "workflow_id": workflow_id,
        "status": QIEJobStatus.PENDING.value,
        "progress": 0.0,
        "current_stage": "pending",
        "message": "분석 시작 대기 중...",
        "total_responses": len(responses),
        "processed_count": 0,
        "_created_at": started_at,
    }

    # Get product description
    product_desc = ""
    if workflow.product:
        product_desc = workflow.product.full_description or workflow.product.name or ""

    # Start background task
    background_tasks.add_task(
        run_qie_analysis_task,
        job_id=job_id,
        workflow_id=workflow_id,
        responses=responses,
        product_description=product_desc,
    )

    return QIEJobResponse(
        job_id=job_id,
        workflow_id=workflow_id,
        status=QIEJobStatus.PENDING.value,
        progress=0.0,
        current_stage="pending",
        message="분석 시작 대기 중...",
        total_responses=len(responses),
        processed_count=0,
        started_at=started_at.isoformat(),
    )


async def run_qie_analysis_task(
    job_id: str,
    workflow_id: str,
    responses: list[dict],
    product_description: str,
):
    """Background task to run QIE analysis."""

    async def progress_callback(stage: str, progress: float, message: str):
        """Update job progress."""
        status_map = {
            "tier1_processing": QIEJobStatus.TIER1_PROCESSING.value,
            "aggregating": QIEJobStatus.AGGREGATING.value,
            "tier2_synthesis": QIEJobStatus.TIER2_SYNTHESIS.value,
            "completed": QIEJobStatus.COMPLETED.value,
        }

        status = status_map.get(stage, QIEJobStatus.TIER1_PROCESSING.value)
        processed = int(progress * len(responses))

        # Update in-memory status for WebSocket
        if job_id in _qie_jobs:
            _qie_jobs[job_id].update({
                "status": status,
                "progress": progress,
                "current_stage": stage,
                "message": message,
                "processed_count": processed,
            })

        # Update database (preserves started_at)
        update_qie_job_progress(
            job_id=job_id,
            status=status,
            progress=progress,
            processed_count=processed,
            current_stage=stage,
            message=message,
        )

    try:
        # Run pipeline
        pipeline = QIEPipeline(progress_callback=progress_callback)
        tier1_results, aggregated_stats, analysis, timing = await pipeline.run_full_analysis(
            responses=responses,
            product_description=product_description,
        )

        # Convert to dictionaries for storage
        tier1_dicts = [tier1_result_to_dict(r) for r in tier1_results]
        stats_dict = aggregated_stats_to_dict(aggregated_stats)
        analysis_dict = qie_analysis_to_dict(analysis)

        # Save results
        save_qie_result(
            job_id=job_id,
            workflow_id=workflow_id,
            tier1_results=tier1_dicts,
            aggregated_stats=stats_dict,
            analysis=analysis_dict,
            execution_time=timing["total_time"],
            tier1_time=timing["tier1_time"],
            tier2_time=timing["tier2_time"],
        )

        # Update final job status (preserves started_at)
        completion_message = f"분석 완료 (총 {timing['total_time']:.1f}초)"
        update_qie_job_progress(
            job_id=job_id,
            status=QIEJobStatus.COMPLETED.value,
            progress=1.0,
            processed_count=len(responses),
            current_stage="completed",
            message=completion_message,
            completed_at=datetime.now(),
        )

        if job_id in _qie_jobs:
            _qie_jobs[job_id].update({
                "status": QIEJobStatus.COMPLETED.value,
                "progress": 1.0,
                "current_stage": "completed",
                "message": completion_message,
                "processed_count": len(responses),
            })

    except Exception as e:
        # Handle failure
        error_msg = str(e)
        failure_message = f"분석 실패: {error_msg[:100]}"
        update_qie_job_progress(
            job_id=job_id,
            status=QIEJobStatus.FAILED.value,
            progress=0.0,
            processed_count=0,
            current_stage="failed",
            message=failure_message,
            completed_at=datetime.now(),
            error=error_msg,
        )

        if job_id in _qie_jobs:
            _qie_jobs[job_id].update({
                "status": QIEJobStatus.FAILED.value,
                "progress": 0.0,
                "current_stage": "failed",
                "message": failure_message,
                "error": error_msg,
            })


@router.get("/{workflow_id}/qie/status", response_model=QIEJobResponse)
async def get_qie_status(workflow_id: str):
    """Get QIE analysis status for a workflow."""
    # Check in-memory first for real-time updates
    for job_id, job_data in _qie_jobs.items():
        if job_data["workflow_id"] == workflow_id:
            return QIEJobResponse(
                job_id=job_id,
                workflow_id=workflow_id,
                status=job_data["status"],
                progress=job_data["progress"],
                current_stage=job_data.get("current_stage", ""),
                message=job_data.get("message", ""),
                total_responses=job_data.get("total_responses", 0),
                processed_count=job_data.get("processed_count", 0),
                error=job_data.get("error"),
            )

    # Fall back to database
    job = load_qie_job_by_workflow(workflow_id)
    if not job:
        raise HTTPException(status_code=404, detail="No QIE analysis found")

    return QIEJobResponse(
        job_id=job["job_id"],
        workflow_id=workflow_id,
        status=job["status"],
        progress=job["progress"],
        current_stage=job.get("current_stage", ""),
        message=job.get("message", ""),
        total_responses=job.get("total_responses", 0),
        processed_count=job.get("processed_count", 0),
        started_at=job["started_at"].isoformat() if job["started_at"] else None,
        completed_at=job["completed_at"].isoformat() if job["completed_at"] else None,
        error=job.get("error"),
    )


@router.get("/{workflow_id}/qie/result", response_model=QIEResultResponse)
async def get_qie_result(workflow_id: str):
    """Get QIE analysis result for a workflow."""
    result = load_qie_result_by_workflow(workflow_id)
    if not result:
        raise HTTPException(status_code=404, detail="No QIE result found")

    return QIEResultResponse(
        job_id=result["job_id"],
        workflow_id=workflow_id,
        analysis=result["analysis"],
        aggregated_stats=result["aggregated_stats"],
        execution_time=result["execution_time"],
        tier1_time=result["tier1_time"],
        tier2_time=result["tier2_time"],
    )


def get_qie_job_status(workflow_id: str) -> Optional[dict]:
    """Get QIE job status for WebSocket updates.

    Used by websocket_workflow.py for real-time progress streaming.
    """
    # Check in-memory first
    for job_data in _qie_jobs.values():
        if job_data["workflow_id"] == workflow_id:
            return job_data

    # Fall back to database
    return load_qie_job_by_workflow(workflow_id)
