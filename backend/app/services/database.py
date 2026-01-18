"""PostgreSQL database service for workflow persistence using Supabase."""

import json
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from ..models.workflow import (
    SurveyWorkflow,
    WorkflowStatus,
    ProductDescription,
    CorePersona,
    ArchetypeSegment,
)
from ..models.comparison import ConceptInput


def get_database_url() -> str:
    """Get database URL from environment."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return url


@contextmanager
def get_connection():
    """Get database connection context manager."""
    conn = psycopg2.connect(get_database_url(), cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize database schema (tables should be created via migrations)."""
    pass


def _datetime_to_str(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO string."""
    return dt.isoformat() if dt else None


def _str_to_datetime(s) -> Optional[datetime]:
    """Convert ISO string or datetime to datetime."""
    if s is None:
        return None
    if isinstance(s, datetime):
        return s
    return datetime.fromisoformat(s)


def save_workflow(workflow: SurveyWorkflow):
    """Save workflow to database."""
    with get_connection() as conn:
        cur = conn.cursor()
        product_json = workflow.product.model_dump_json() if workflow.product else None
        persona_json = workflow.core_persona.model_dump_json() if workflow.core_persona else None
        concepts_json = json.dumps([c.model_dump() for c in workflow.concepts]) if workflow.concepts else None
        archetypes_json = json.dumps([a.model_dump() for a in workflow.archetypes]) if workflow.archetypes else None

        cur.execute("""
            INSERT INTO workflows (
                id, status, current_step, product_json, core_persona_json,
                concepts_json, archetypes_json, use_multi_archetype, currency,
                sample_size, persona_generation_job_id, survey_execution_job_id,
                error_message, created_at, updated_at, completed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                current_step = EXCLUDED.current_step,
                product_json = EXCLUDED.product_json,
                core_persona_json = EXCLUDED.core_persona_json,
                concepts_json = EXCLUDED.concepts_json,
                archetypes_json = EXCLUDED.archetypes_json,
                use_multi_archetype = EXCLUDED.use_multi_archetype,
                currency = EXCLUDED.currency,
                sample_size = EXCLUDED.sample_size,
                persona_generation_job_id = EXCLUDED.persona_generation_job_id,
                survey_execution_job_id = EXCLUDED.survey_execution_job_id,
                error_message = EXCLUDED.error_message,
                updated_at = EXCLUDED.updated_at,
                completed_at = EXCLUDED.completed_at
        """, (
            workflow.id,
            workflow.status.value,
            workflow.current_step,
            product_json,
            persona_json,
            concepts_json,
            archetypes_json,
            workflow.use_multi_archetype,
            workflow.currency,
            workflow.sample_size,
            workflow.persona_generation_job_id,
            workflow.survey_execution_job_id,
            workflow.error_message,
            _datetime_to_str(workflow.created_at),
            _datetime_to_str(workflow.updated_at),
            _datetime_to_str(workflow.completed_at),
        ))


def load_workflow(workflow_id: str) -> Optional[SurveyWorkflow]:
    """Load workflow from database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM workflows WHERE id = %s", (workflow_id,))
        row = cur.fetchone()

        if not row:
            return None

        product = None
        if row["product_json"]:
            product = ProductDescription.model_validate_json(row["product_json"])

        core_persona = None
        if row["core_persona_json"]:
            core_persona = CorePersona.model_validate_json(row["core_persona_json"])

        concepts = []
        if row.get("concepts_json"):
            concepts_data = json.loads(row["concepts_json"])
            concepts = [ConceptInput.model_validate(c) for c in concepts_data]

        archetypes = []
        if row.get("archetypes_json"):
            archetypes_data = json.loads(row["archetypes_json"])
            archetypes = [ArchetypeSegment.model_validate(a) for a in archetypes_data]

        use_multi_archetype = bool(row.get("use_multi_archetype", False))
        currency = row.get("currency") or "KRW"

        return SurveyWorkflow(
            id=row["id"],
            status=WorkflowStatus(row["status"]),
            current_step=row["current_step"],
            product=product,
            core_persona=core_persona,
            concepts=concepts,
            archetypes=archetypes,
            use_multi_archetype=use_multi_archetype,
            currency=currency,
            sample_size=row["sample_size"],
            persona_generation_job_id=row["persona_generation_job_id"],
            survey_execution_job_id=row["survey_execution_job_id"],
            error_message=row["error_message"],
            created_at=_str_to_datetime(row["created_at"]),
            updated_at=_str_to_datetime(row["updated_at"]),
            completed_at=_str_to_datetime(row["completed_at"]),
        )


def load_all_workflows() -> list[SurveyWorkflow]:
    """Load all workflows from database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM workflows ORDER BY created_at DESC")
        rows = cur.fetchall()
        workflows = []
        for row in rows:
            workflow = load_workflow(row["id"])
            if workflow:
                workflows.append(workflow)
        return workflows


def delete_workflow(workflow_id: str):
    """Delete workflow from database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM workflows WHERE id = %s", (workflow_id,))


def save_generation_job(job_id: str, workflow_id: str, status: str,
                        total_personas: int, generated_count: int,
                        progress: float, started_at: datetime,
                        completed_at: Optional[datetime] = None,
                        error: Optional[str] = None):
    """Save generation job status to database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO generation_jobs (
                job_id, workflow_id, status, total_personas, generated_count,
                progress, started_at, completed_at, error
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_id) DO UPDATE SET
                status = EXCLUDED.status,
                total_personas = EXCLUDED.total_personas,
                generated_count = EXCLUDED.generated_count,
                progress = EXCLUDED.progress,
                completed_at = EXCLUDED.completed_at,
                error = EXCLUDED.error
        """, (
            job_id, workflow_id, status, total_personas, generated_count,
            progress, _datetime_to_str(started_at),
            _datetime_to_str(completed_at), error
        ))


def load_generation_job(job_id: str) -> Optional[dict]:
    """Load generation job from database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM generation_jobs WHERE job_id = %s", (job_id,))
        row = cur.fetchone()

        if not row:
            return None

        return {
            "job_id": row["job_id"],
            "workflow_id": row["workflow_id"],
            "status": row["status"],
            "total_personas": row["total_personas"],
            "generated_count": row["generated_count"],
            "progress": row["progress"],
            "started_at": _str_to_datetime(row["started_at"]),
            "completed_at": _str_to_datetime(row["completed_at"]),
            "error": row["error"],
        }


def save_generation_result(job_id: str, workflow_id: str,
                           total_personas: int, distribution_stats: dict,
                           personas: list[dict]):
    """Save generation result to database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO generation_results (
                job_id, workflow_id, total_personas,
                distribution_stats_json, personas_json
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (job_id) DO UPDATE SET
                total_personas = EXCLUDED.total_personas,
                distribution_stats_json = EXCLUDED.distribution_stats_json,
                personas_json = EXCLUDED.personas_json
        """, (
            job_id, workflow_id, total_personas,
            json.dumps(distribution_stats),
            json.dumps(personas)
        ))


def load_generation_result(job_id: str) -> Optional[dict]:
    """Load generation result from database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM generation_results WHERE job_id = %s", (job_id,))
        row = cur.fetchone()

        if not row:
            return None

        return {
            "job_id": row["job_id"],
            "workflow_id": row["workflow_id"],
            "total_personas": row["total_personas"],
            "distribution_stats": json.loads(row["distribution_stats_json"]),
            "personas": json.loads(row["personas_json"]),
        }


def save_execution_job(job_id: str, workflow_id: str, status: str,
                       total_respondents: int, completed_count: int,
                       progress: float, started_at: datetime,
                       completed_at: Optional[datetime] = None,
                       error: Optional[str] = None):
    """Save execution job status to database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO execution_jobs (
                job_id, workflow_id, status, total_respondents, completed_count,
                progress, started_at, completed_at, error
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_id) DO UPDATE SET
                status = EXCLUDED.status,
                total_respondents = EXCLUDED.total_respondents,
                completed_count = EXCLUDED.completed_count,
                progress = EXCLUDED.progress,
                completed_at = EXCLUDED.completed_at,
                error = EXCLUDED.error
        """, (
            job_id, workflow_id, status, total_respondents, completed_count,
            progress, _datetime_to_str(started_at),
            _datetime_to_str(completed_at), error
        ))


def load_execution_job(job_id: str) -> Optional[dict]:
    """Load execution job from database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM execution_jobs WHERE job_id = %s", (job_id,))
        row = cur.fetchone()

        if not row:
            return None

        return {
            "job_id": row["job_id"],
            "workflow_id": row["workflow_id"],
            "status": row["status"],
            "total_respondents": row["total_respondents"],
            "completed_count": row["completed_count"],
            "progress": row["progress"],
            "started_at": _str_to_datetime(row["started_at"]),
            "completed_at": _str_to_datetime(row["completed_at"]),
            "error": row["error"],
        }


def save_execution_result(
    job_id: str,
    workflow_id: str,
    total_respondents: int,
    execution_time: float,
    mean_score: float,
    median_score: float,
    std_dev: float,
    score_distribution: dict,
    results: list[dict],
    comparison_mode: str = "single",
    concept_scores: Optional[list] = None,
    comparison_stats: Optional[dict] = None,
    quick_insight: Optional[dict] = None,
):
    """Save execution result to database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO execution_results (
                job_id, workflow_id, total_respondents, execution_time,
                mean_score, median_score, std_dev,
                score_distribution_json, results_json,
                comparison_mode, concept_scores_json,
                comparison_stats_json, quick_insight_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_id) DO UPDATE SET
                total_respondents = EXCLUDED.total_respondents,
                execution_time = EXCLUDED.execution_time,
                mean_score = EXCLUDED.mean_score,
                median_score = EXCLUDED.median_score,
                std_dev = EXCLUDED.std_dev,
                score_distribution_json = EXCLUDED.score_distribution_json,
                results_json = EXCLUDED.results_json,
                comparison_mode = EXCLUDED.comparison_mode,
                concept_scores_json = EXCLUDED.concept_scores_json,
                comparison_stats_json = EXCLUDED.comparison_stats_json,
                quick_insight_json = EXCLUDED.quick_insight_json
        """, (
            job_id, workflow_id, total_respondents, execution_time,
            mean_score, median_score, std_dev,
            json.dumps(score_distribution),
            json.dumps(results),
            comparison_mode,
            json.dumps(concept_scores) if concept_scores else None,
            json.dumps(comparison_stats) if comparison_stats else None,
            json.dumps(quick_insight) if quick_insight else None,
        ))


def load_execution_result(job_id: str) -> Optional[dict]:
    """Load execution result from database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM execution_results WHERE job_id = %s", (job_id,))
        row = cur.fetchone()

        if not row:
            return None

        return {
            "job_id": row["job_id"],
            "workflow_id": row["workflow_id"],
            "total_respondents": row["total_respondents"],
            "execution_time": row["execution_time"],
            "mean_score": row["mean_score"],
            "median_score": row["median_score"],
            "std_dev": row["std_dev"],
            "score_distribution": json.loads(row["score_distribution_json"]),
            "results": json.loads(row["results_json"]),
            "comparison_mode": row.get("comparison_mode") or "single",
            "concept_scores": json.loads(row["concept_scores_json"]) if row.get("concept_scores_json") else None,
            "comparison_stats": json.loads(row["comparison_stats_json"]) if row.get("comparison_stats_json") else None,
            "quick_insight": json.loads(row["quick_insight_json"]) if row.get("quick_insight_json") else None,
        }


# QIE (Qualitative Insight Engine) database functions

def save_qie_job(
    job_id: str,
    workflow_id: str,
    status: str,
    progress: float,
    total_responses: int,
    processed_count: int,
    started_at: datetime,
    current_stage: str = "",
    message: str = "",
    completed_at: Optional[datetime] = None,
    error: Optional[str] = None,
):
    """Save QIE job status to database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO qie_jobs (
                job_id, workflow_id, status, progress, current_stage, message,
                total_responses, processed_count, started_at, completed_at, error
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_id) DO UPDATE SET
                status = EXCLUDED.status,
                progress = EXCLUDED.progress,
                current_stage = EXCLUDED.current_stage,
                message = EXCLUDED.message,
                total_responses = EXCLUDED.total_responses,
                processed_count = EXCLUDED.processed_count,
                completed_at = EXCLUDED.completed_at,
                error = EXCLUDED.error
        """, (
            job_id,
            workflow_id,
            status,
            progress,
            current_stage,
            message,
            total_responses,
            processed_count,
            _datetime_to_str(started_at),
            _datetime_to_str(completed_at),
            error,
        ))


def load_qie_job(job_id: str) -> Optional[dict]:
    """Load QIE job from database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM qie_jobs WHERE job_id = %s", (job_id,))
        row = cur.fetchone()

        if not row:
            return None

        return {
            "job_id": row["job_id"],
            "workflow_id": row["workflow_id"],
            "status": row["status"],
            "progress": row["progress"],
            "current_stage": row["current_stage"],
            "message": row["message"],
            "total_responses": row["total_responses"],
            "processed_count": row["processed_count"],
            "started_at": _str_to_datetime(row["started_at"]),
            "completed_at": _str_to_datetime(row["completed_at"]),
            "error": row["error"],
        }


def load_qie_job_by_workflow(workflow_id: str) -> Optional[dict]:
    """Load most recent QIE job for a workflow."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM qie_jobs WHERE workflow_id = %s ORDER BY started_at DESC LIMIT 1",
            (workflow_id,),
        )
        row = cur.fetchone()

        if not row:
            return None

        return {
            "job_id": row["job_id"],
            "workflow_id": row["workflow_id"],
            "status": row["status"],
            "progress": row["progress"],
            "current_stage": row["current_stage"],
            "message": row["message"],
            "total_responses": row["total_responses"],
            "processed_count": row["processed_count"],
            "started_at": _str_to_datetime(row["started_at"]),
            "completed_at": _str_to_datetime(row["completed_at"]),
            "error": row["error"],
        }


def update_qie_job_progress(
    job_id: str,
    status: str,
    progress: float,
    processed_count: int,
    current_stage: str = "",
    message: str = "",
    completed_at: Optional[datetime] = None,
    error: Optional[str] = None,
):
    """Update QIE job progress without overwriting started_at."""
    with get_connection() as conn:
        cur = conn.cursor()
        if completed_at:
            cur.execute("""
                UPDATE qie_jobs SET
                    status = %s, progress = %s, processed_count = %s,
                    current_stage = %s, message = %s, completed_at = %s, error = %s
                WHERE job_id = %s
            """, (
                status,
                progress,
                processed_count,
                current_stage,
                message,
                _datetime_to_str(completed_at),
                error,
                job_id,
            ))
        else:
            cur.execute("""
                UPDATE qie_jobs SET
                    status = %s, progress = %s, processed_count = %s,
                    current_stage = %s, message = %s, error = %s
                WHERE job_id = %s
            """, (
                status,
                progress,
                processed_count,
                current_stage,
                message,
                error,
                job_id,
            ))


def save_qie_result(
    job_id: str,
    workflow_id: str,
    tier1_results: list[dict],
    aggregated_stats: dict,
    analysis: dict,
    execution_time: float,
    tier1_time: float,
    tier2_time: float,
    report_data: Optional[dict] = None,
    report_generation_time: float = 0.0,
):
    """Save QIE result to database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO qie_results (
                job_id, workflow_id, tier1_results_json, aggregated_stats_json,
                analysis_json, execution_time, tier1_time, tier2_time,
                report_data_json, report_generation_time, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_id) DO UPDATE SET
                tier1_results_json = EXCLUDED.tier1_results_json,
                aggregated_stats_json = EXCLUDED.aggregated_stats_json,
                analysis_json = EXCLUDED.analysis_json,
                execution_time = EXCLUDED.execution_time,
                tier1_time = EXCLUDED.tier1_time,
                tier2_time = EXCLUDED.tier2_time,
                report_data_json = EXCLUDED.report_data_json,
                report_generation_time = EXCLUDED.report_generation_time
        """, (
            job_id,
            workflow_id,
            json.dumps(tier1_results),
            json.dumps(aggregated_stats),
            json.dumps(analysis),
            execution_time,
            tier1_time,
            tier2_time,
            json.dumps(report_data) if report_data else None,
            report_generation_time,
            _datetime_to_str(datetime.now()),
        ))


def load_qie_result(job_id: str) -> Optional[dict]:
    """Load QIE result from database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM qie_results WHERE job_id = %s", (job_id,))
        row = cur.fetchone()

        if not row:
            return None

        return {
            "job_id": row["job_id"],
            "workflow_id": row["workflow_id"],
            "tier1_results": json.loads(row["tier1_results_json"]),
            "aggregated_stats": json.loads(row["aggregated_stats_json"]),
            "analysis": json.loads(row["analysis_json"]),
            "execution_time": row["execution_time"],
            "tier1_time": row["tier1_time"],
            "tier2_time": row["tier2_time"],
            "report_data": json.loads(row["report_data_json"]) if row.get("report_data_json") else None,
            "report_generation_time": row.get("report_generation_time"),
            "created_at": _str_to_datetime(row["created_at"]),
        }


def load_qie_result_by_workflow(workflow_id: str) -> Optional[dict]:
    """Load most recent QIE result for a workflow."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM qie_results WHERE workflow_id = %s ORDER BY created_at DESC LIMIT 1",
            (workflow_id,),
        )
        row = cur.fetchone()

        if not row:
            return None

        return {
            "job_id": row["job_id"],
            "workflow_id": row["workflow_id"],
            "tier1_results": json.loads(row["tier1_results_json"]),
            "aggregated_stats": json.loads(row["aggregated_stats_json"]),
            "analysis": json.loads(row["analysis_json"]),
            "execution_time": row["execution_time"],
            "tier1_time": row["tier1_time"],
            "tier2_time": row["tier2_time"],
            "report_data": json.loads(row["report_data_json"]) if row.get("report_data_json") else None,
            "report_generation_time": row.get("report_generation_time"),
            "created_at": _str_to_datetime(row["created_at"]),
        }


# Initialize database on module import (no-op for PostgreSQL, schema via migrations)
init_database()
