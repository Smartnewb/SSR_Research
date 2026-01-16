"""Survey execution API routes for workflow."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from scipy import stats
import numpy as np

from ..services.survey import SurveyService
from ..services.workflow import get_workflow_service
from ..services.persona_generation import persona_to_system_prompt
from ..services import database as db
from ..models.comparison import ConceptInput
from ..routes.generation import (
    _generation_results,
    _load_result_from_db as _load_generation_result_from_db,
)

router = APIRouter(prefix="/api/workflows/{workflow_id}/execute", tags=["execution"])


class ExecutionStatus(BaseModel):
    """Status of survey execution."""

    job_id: str
    workflow_id: str
    status: str
    total_respondents: int
    completed_count: int
    progress: float
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None


class ConceptScore(BaseModel):
    """Score for a single concept."""

    concept_id: str
    concept_title: str
    mean_score: float
    median_score: float
    std_dev: float
    score_distribution: dict
    results: list[dict]


class ComparisonStatistics(BaseModel):
    """Statistical comparison between concepts."""

    test_type: str  # "none", "t_test", "anova"
    statistic: Optional[float] = None
    p_value: Optional[float] = None
    is_significant: bool = False
    winner: Optional[str] = None
    interpretation: str = ""


class ExecutionResult(BaseModel):
    """Result of survey execution."""

    job_id: str
    workflow_id: str
    total_respondents: int
    execution_time: float
    # Single concept results (backward compatible)
    mean_score: float
    median_score: float
    std_dev: float
    score_distribution: dict
    results: list[dict]
    # Multi-concept comparison results
    comparison_mode: str = "single"  # "single", "ab_test", "multi_compare"
    concept_scores: Optional[list[ConceptScore]] = None
    comparison_stats: Optional[ComparisonStatistics] = None


# In-memory cache for active jobs
_execution_jobs: dict[str, ExecutionStatus] = {}
_execution_results: dict[str, ExecutionResult] = {}


def _save_job_to_db(status: ExecutionStatus):
    """Save job status to database."""
    db.save_execution_job(
        job_id=status.job_id,
        workflow_id=status.workflow_id,
        status=status.status,
        total_respondents=status.total_respondents,
        completed_count=status.completed_count,
        progress=status.progress,
        started_at=status.started_at,
        completed_at=status.completed_at,
        error=status.error,
    )


def _load_job_from_db(job_id: str) -> ExecutionStatus | None:
    """Load job status from database."""
    data = db.load_execution_job(job_id)
    if not data:
        return None
    return ExecutionStatus(**data)


def _save_result_to_db(result: ExecutionResult):
    """Save result to database."""
    db.save_execution_result(
        job_id=result.job_id,
        workflow_id=result.workflow_id,
        total_respondents=result.total_respondents,
        execution_time=result.execution_time,
        mean_score=result.mean_score,
        median_score=result.median_score,
        std_dev=result.std_dev,
        score_distribution=result.score_distribution,
        results=result.results,
    )


def _load_result_from_db(job_id: str) -> ExecutionResult | None:
    """Load result from database."""
    data = db.load_execution_result(job_id)
    if not data:
        return None
    return ExecutionResult(**data)


def _calculate_stats(scores: list[float]) -> tuple[float, float, float, dict]:
    """Calculate statistics for a list of scores."""
    mean_score = sum(scores) / len(scores) if scores else 0
    sorted_scores = sorted(scores)
    median_score = sorted_scores[len(scores) // 2] if scores else 0
    std_dev = (sum((s - mean_score) ** 2 for s in scores) / len(scores)) ** 0.5 if scores else 0

    score_distribution = {}
    for score in scores:
        bucket = f"{int(score * 10) / 10:.1f}"
        score_distribution[bucket] = score_distribution.get(bucket, 0) + 1

    return mean_score, median_score, std_dev, score_distribution


def _calculate_comparison_stats(
    concept_scores: list[ConceptScore],
) -> ComparisonStatistics:
    """Calculate statistical comparison between concepts."""
    if len(concept_scores) < 2:
        return ComparisonStatistics(
            test_type="none",
            interpretation="Single concept - no comparison needed",
        )

    # Extract all scores per concept
    all_scores = []
    for cs in concept_scores:
        scores = [r["ssr_score"] for r in cs.results]
        all_scores.append(scores)

    if len(concept_scores) == 2:
        # A/B Testing: t-test
        t_stat, p_value = stats.ttest_ind(all_scores[0], all_scores[1])
        is_significant = p_value < 0.05

        if is_significant:
            winner_idx = 0 if concept_scores[0].mean_score > concept_scores[1].mean_score else 1
            winner = concept_scores[winner_idx].concept_title
            interpretation = f"{winner} significantly outperforms the other (p={p_value:.4f})"
        else:
            winner = None
            interpretation = f"No significant difference between concepts (p={p_value:.4f})"

        return ComparisonStatistics(
            test_type="t_test",
            statistic=float(t_stat),
            p_value=float(p_value),
            is_significant=is_significant,
            winner=winner,
            interpretation=interpretation,
        )
    else:
        # Multi-concept: ANOVA
        f_stat, p_value = stats.f_oneway(*all_scores)
        is_significant = p_value < 0.05

        if is_significant:
            winner_idx = max(range(len(concept_scores)), key=lambda i: concept_scores[i].mean_score)
            winner = concept_scores[winner_idx].concept_title
            interpretation = f"{winner} has the highest score with significant difference (p={p_value:.4f})"
        else:
            winner = None
            interpretation = f"No significant difference between concepts (p={p_value:.4f})"

        return ComparisonStatistics(
            test_type="anova",
            statistic=float(f_stat),
            p_value=float(p_value),
            is_significant=is_significant,
            winner=winner,
            interpretation=interpretation,
        )


async def _execute_single_concept_survey(
    concept_id: str,
    concept_title: str,
    product_description: str,
    personas: list[dict],
    use_mock: bool,
    progress_callback=None,
) -> ConceptScore:
    """Execute survey for a single concept and return scores."""
    results = []

    for i, persona in enumerate(personas):
        system_prompt = persona_to_system_prompt(persona)

        if use_mock:
            await asyncio.sleep(0.01)
            # Vary mock scores slightly by concept to show difference
            base_score = 0.5 + hash(concept_id) % 30 / 100
            ssr_score = base_score + (i % 10) * 0.02
            ssr_score = min(max(ssr_score, 0.0), 1.0)
            response_text = f"Mock response from persona {persona['id']} for {concept_title}"
        else:
            from src.pipeline import SSRPipeline

            pipeline = SSRPipeline()
            result = await asyncio.to_thread(
                pipeline.survey_single_persona,
                product_description=product_description,
                persona_data=persona,
                system_prompt=system_prompt,
            )
            ssr_score = result.ssr_score
            response_text = result.response_text

        results.append({
            "persona_id": persona["id"],
            "concept_id": concept_id,
            "demographics": {
                "age": persona["age"],
                "gender": persona["gender"],
                "income": persona["income_bracket"],
                "location": persona["location"],
            },
            "response_text": response_text,
            "ssr_score": ssr_score,
        })

        if progress_callback:
            progress_callback(i + 1)

    scores = [r["ssr_score"] for r in results]
    mean_score, median_score, std_dev, score_distribution = _calculate_stats(scores)

    return ConceptScore(
        concept_id=concept_id,
        concept_title=concept_title,
        mean_score=mean_score,
        median_score=median_score,
        std_dev=std_dev,
        score_distribution=score_distribution,
        results=results,
    )


async def _execute_survey_background(
    job_id: str,
    workflow_id: str,
    concepts: list[ConceptInput],
    personas: list[dict],
    use_mock: bool,
):
    """Background task for executing survey with concept comparison support."""
    try:
        _execution_jobs[job_id].status = "executing"
        _save_job_to_db(_execution_jobs[job_id])

        import time
        start_time = time.time()

        total_tasks = len(concepts) * len(personas)
        completed_tasks = 0

        def update_progress(count: int):
            nonlocal completed_tasks
            completed_tasks += 1
            _execution_jobs[job_id].completed_count = completed_tasks
            _execution_jobs[job_id].progress = completed_tasks / total_tasks

        # Execute survey for each concept
        concept_scores = []
        for concept in concepts:
            concept_score = await _execute_single_concept_survey(
                concept_id=concept.id,
                concept_title=concept.title,
                product_description=f"{concept.headline}\n\n{concept.benefit}\n\nReason to believe: {concept.rtb}\n\nPrice: {concept.price}",
                personas=personas,
                use_mock=use_mock,
                progress_callback=update_progress,
            )
            concept_scores.append(concept_score)

        execution_time = time.time() - start_time

        # Determine comparison mode
        if len(concepts) == 1:
            comparison_mode = "single"
        elif len(concepts) == 2:
            comparison_mode = "ab_test"
        else:
            comparison_mode = "multi_compare"

        # Calculate comparison statistics
        comparison_stats = _calculate_comparison_stats(concept_scores)

        # For backward compatibility, use first concept's scores as main scores
        main_scores = concept_scores[0]
        all_results = []
        for cs in concept_scores:
            all_results.extend(cs.results)

        _execution_jobs[job_id].status = "completed"
        _execution_jobs[job_id].completed_at = datetime.now(timezone.utc)
        _save_job_to_db(_execution_jobs[job_id])

        exec_result = ExecutionResult(
            job_id=job_id,
            workflow_id=workflow_id,
            total_respondents=len(personas) * len(concepts),
            execution_time=execution_time,
            # Backward compatible fields (use first concept or average)
            mean_score=main_scores.mean_score,
            median_score=main_scores.median_score,
            std_dev=main_scores.std_dev,
            score_distribution=main_scores.score_distribution,
            results=all_results,
            # New comparison fields
            comparison_mode=comparison_mode,
            concept_scores=concept_scores,
            comparison_stats=comparison_stats,
        )
        _execution_results[job_id] = exec_result
        _save_result_to_db(exec_result)

        workflow_service = get_workflow_service()
        workflow_service.complete_survey(workflow_id)

    except Exception as e:
        _execution_jobs[job_id].status = "failed"
        _execution_jobs[job_id].error = str(e)
        _save_job_to_db(_execution_jobs[job_id])

        workflow_service = get_workflow_service()
        workflow_service.fail_workflow(workflow_id, f"Survey execution failed: {e}")


@router.post("/start", response_model=ExecutionStatus)
async def start_execution(
    workflow_id: str, background_tasks: BackgroundTasks, use_mock: bool = False
):
    """Start survey execution (Step 7).

    This triggers background execution of the survey with all generated personas.
    Supports single concept, A/B testing (2 concepts), and multi-compare (3-5 concepts).
    """
    workflow_service = get_workflow_service()
    workflow = workflow_service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not workflow.product:
        raise HTTPException(status_code=400, detail="Product not set")

    if not workflow.persona_generation_job_id:
        raise HTTPException(status_code=400, detail="Personas not generated")

    gen_job_id = workflow.persona_generation_job_id

    # Try memory cache first, then database
    generation_result = _generation_results.get(gen_job_id)
    if not generation_result:
        generation_result = _load_generation_result_from_db(gen_job_id)
        if generation_result:
            _generation_results[gen_job_id] = generation_result

    if not generation_result:
        raise HTTPException(status_code=400, detail="Generation result not found")

    # Prepare concepts - use workflow concepts or create from product
    concepts = workflow.concepts
    if not concepts:
        # Auto-create concept from product if none exist
        concepts = [ConceptInput(
            id="CONCEPT_001",
            title=workflow.product.name,
            headline=workflow.product.description[:200] if len(workflow.product.description) > 200 else workflow.product.description,
            consumer_insight=f"Target market: {workflow.product.target_market}",
            benefit=", ".join(workflow.product.features[:3]) if workflow.product.features else "Key benefits",
            rtb=f"Category: {workflow.product.category}",
            image_description=f"Visual representation of {workflow.product.name}",
            price=workflow.product.price_point or "Contact for pricing",
        )]

    # Calculate total respondents (personas * concepts)
    total_respondents = len(generation_result.personas) * len(concepts)

    job_id = f"EXEC_{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    status = ExecutionStatus(
        job_id=job_id,
        workflow_id=workflow_id,
        status="queued",
        total_respondents=total_respondents,
        completed_count=0,
        progress=0.0,
        started_at=now,
    )

    _execution_jobs[job_id] = status
    _save_job_to_db(status)

    workflow_service.start_survey_execution(workflow_id, job_id)

    background_tasks.add_task(
        _execute_survey_background,
        job_id,
        workflow_id,
        concepts,
        generation_result.personas,
        use_mock,
    )

    return status


@router.get("/status", response_model=ExecutionStatus)
async def get_execution_status(workflow_id: str):
    """Get survey execution status.

    Check the progress of survey execution.
    """
    workflow_service = get_workflow_service()
    workflow = workflow_service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not workflow.survey_execution_job_id:
        raise HTTPException(status_code=404, detail="No execution job found")

    job_id = workflow.survey_execution_job_id

    # Try memory cache first
    status = _execution_jobs.get(job_id)

    # Try database if not in memory
    if not status:
        status = _load_job_from_db(job_id)
        if status:
            _execution_jobs[job_id] = status

    if not status:
        raise HTTPException(status_code=404, detail="Execution job not found")

    return status


@router.get("/result", response_model=ExecutionResult)
async def get_execution_result(workflow_id: str):
    """Get survey execution result (Step 7).

    Returns the final survey results including SSR scores and responses.
    """
    workflow_service = get_workflow_service()
    workflow = workflow_service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not workflow.survey_execution_job_id:
        raise HTTPException(status_code=404, detail="No execution job found")

    job_id = workflow.survey_execution_job_id

    # Try memory cache first
    result = _execution_results.get(job_id)

    # Try database if not in memory
    if not result:
        result = _load_result_from_db(job_id)
        if result:
            _execution_results[job_id] = result

    if not result:
        status = _execution_jobs.get(job_id) or _load_job_from_db(job_id)
        if status and status.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Execution not completed. Status: {status.status}",
            )
        raise HTTPException(status_code=404, detail="Execution result not found")

    return result
