"""SQLite database service for workflow persistence."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models.workflow import (
    SurveyWorkflow,
    WorkflowStatus,
    ProductDescription,
    CorePersona,
)
from ..models.comparison import ConceptInput

DB_PATH = Path(__file__).parent.parent.parent / "data" / "workflows.db"


def get_db_path() -> Path:
    """Get database path, creating directory if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


@contextmanager
def get_connection():
    """Get database connection context manager."""
    conn = sqlite3.connect(get_db_path(), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_database():
    """Initialize database schema."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                current_step INTEGER NOT NULL,
                product_json TEXT,
                core_persona_json TEXT,
                concepts_json TEXT,
                sample_size INTEGER,
                persona_generation_job_id TEXT,
                survey_execution_job_id TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)

        # Migration: Add concepts_json column if it doesn't exist
        try:
            conn.execute("ALTER TABLE workflows ADD COLUMN concepts_json TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.execute("""
            CREATE TABLE IF NOT EXISTS generation_jobs (
                job_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                status TEXT NOT NULL,
                total_personas INTEGER NOT NULL,
                generated_count INTEGER NOT NULL,
                progress REAL NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                error TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS generation_results (
                job_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                total_personas INTEGER NOT NULL,
                distribution_stats_json TEXT NOT NULL,
                personas_json TEXT NOT NULL,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS execution_jobs (
                job_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                status TEXT NOT NULL,
                total_respondents INTEGER NOT NULL,
                completed_count INTEGER NOT NULL,
                progress REAL NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                error TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS execution_results (
                job_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                total_respondents INTEGER NOT NULL,
                execution_time REAL NOT NULL,
                mean_score REAL NOT NULL,
                median_score REAL NOT NULL,
                std_dev REAL NOT NULL,
                score_distribution_json TEXT NOT NULL,
                results_json TEXT NOT NULL,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id)
            )
        """)


def _datetime_to_str(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO string."""
    return dt.isoformat() if dt else None


def _str_to_datetime(s: Optional[str]) -> Optional[datetime]:
    """Convert ISO string to datetime."""
    return datetime.fromisoformat(s) if s else None


def save_workflow(workflow: SurveyWorkflow):
    """Save workflow to database."""
    with get_connection() as conn:
        product_json = workflow.product.model_dump_json() if workflow.product else None
        persona_json = workflow.core_persona.model_dump_json() if workflow.core_persona else None
        concepts_json = json.dumps([c.model_dump() for c in workflow.concepts]) if workflow.concepts else None

        conn.execute("""
            INSERT OR REPLACE INTO workflows (
                id, status, current_step, product_json, core_persona_json,
                concepts_json, sample_size, persona_generation_job_id, survey_execution_job_id,
                error_message, created_at, updated_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow.id,
            workflow.status.value,
            workflow.current_step,
            product_json,
            persona_json,
            concepts_json,
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
        row = conn.execute(
            "SELECT * FROM workflows WHERE id = ?",
            (workflow_id,)
        ).fetchone()

        if not row:
            return None

        product = None
        if row["product_json"]:
            product = ProductDescription.model_validate_json(row["product_json"])

        core_persona = None
        if row["core_persona_json"]:
            core_persona = CorePersona.model_validate_json(row["core_persona_json"])

        concepts = []
        concepts_json_value = row["concepts_json"] if "concepts_json" in row.keys() else None
        if concepts_json_value:
            concepts_data = json.loads(concepts_json_value)
            concepts = [ConceptInput.model_validate(c) for c in concepts_data]

        return SurveyWorkflow(
            id=row["id"],
            status=WorkflowStatus(row["status"]),
            current_step=row["current_step"],
            product=product,
            core_persona=core_persona,
            concepts=concepts,
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
        rows = conn.execute("SELECT id FROM workflows ORDER BY created_at DESC").fetchall()
        workflows = []
        for row in rows:
            workflow = load_workflow(row["id"])
            if workflow:
                workflows.append(workflow)
        return workflows


def delete_workflow(workflow_id: str):
    """Delete workflow from database."""
    with get_connection() as conn:
        conn.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))


def save_generation_job(job_id: str, workflow_id: str, status: str,
                        total_personas: int, generated_count: int,
                        progress: float, started_at: datetime,
                        completed_at: Optional[datetime] = None,
                        error: Optional[str] = None):
    """Save generation job status to database."""
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO generation_jobs (
                job_id, workflow_id, status, total_personas, generated_count,
                progress, started_at, completed_at, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id, workflow_id, status, total_personas, generated_count,
            progress, _datetime_to_str(started_at),
            _datetime_to_str(completed_at), error
        ))


def load_generation_job(job_id: str) -> Optional[dict]:
    """Load generation job from database."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM generation_jobs WHERE job_id = ?",
            (job_id,)
        ).fetchone()

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
        conn.execute("""
            INSERT OR REPLACE INTO generation_results (
                job_id, workflow_id, total_personas,
                distribution_stats_json, personas_json
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            job_id, workflow_id, total_personas,
            json.dumps(distribution_stats),
            json.dumps(personas)
        ))


def load_generation_result(job_id: str) -> Optional[dict]:
    """Load generation result from database."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM generation_results WHERE job_id = ?",
            (job_id,)
        ).fetchone()

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
        conn.execute("""
            INSERT OR REPLACE INTO execution_jobs (
                job_id, workflow_id, status, total_respondents, completed_count,
                progress, started_at, completed_at, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id, workflow_id, status, total_respondents, completed_count,
            progress, _datetime_to_str(started_at),
            _datetime_to_str(completed_at), error
        ))


def load_execution_job(job_id: str) -> Optional[dict]:
    """Load execution job from database."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM execution_jobs WHERE job_id = ?",
            (job_id,)
        ).fetchone()

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


def save_execution_result(job_id: str, workflow_id: str,
                          total_respondents: int, execution_time: float,
                          mean_score: float, median_score: float,
                          std_dev: float, score_distribution: dict,
                          results: list[dict]):
    """Save execution result to database."""
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO execution_results (
                job_id, workflow_id, total_respondents, execution_time,
                mean_score, median_score, std_dev,
                score_distribution_json, results_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id, workflow_id, total_respondents, execution_time,
            mean_score, median_score, std_dev,
            json.dumps(score_distribution),
            json.dumps(results)
        ))


def load_execution_result(job_id: str) -> Optional[dict]:
    """Load execution result from database."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM execution_results WHERE job_id = ?",
            (job_id,)
        ).fetchone()

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
        }


# Initialize database on module import
init_database()
