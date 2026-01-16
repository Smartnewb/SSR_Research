"""Survey workflow service with SQLite persistence."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from ..models.workflow import (
    SurveyWorkflow,
    WorkflowStatus,
    ProductDescription,
    CorePersona,
)
from ..models.comparison import ConceptInput
from . import database as db


class WorkflowService:
    """Service for managing survey workflows with database persistence."""

    def __init__(self):
        self._workflows: dict[str, SurveyWorkflow] = {}
        self._load_from_database()

    def _load_from_database(self):
        """Load all workflows from database into memory cache."""
        workflows = db.load_all_workflows()
        for workflow in workflows:
            self._workflows[workflow.id] = workflow

    def _save_to_database(self, workflow: SurveyWorkflow):
        """Save workflow to database."""
        db.save_workflow(workflow)

    def create_workflow(self) -> SurveyWorkflow:
        """Create a new survey workflow."""
        workflow_id = f"WF_{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now(timezone.utc)

        workflow = SurveyWorkflow(
            id=workflow_id,
            status=WorkflowStatus.PRODUCT_INPUT,
            current_step=1,
            created_at=now,
            updated_at=now,
        )

        self._workflows[workflow_id] = workflow
        self._save_to_database(workflow)
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[SurveyWorkflow]:
        """Get workflow by ID."""
        # Try memory cache first
        if workflow_id in self._workflows:
            return self._workflows[workflow_id]

        # Try loading from database
        workflow = db.load_workflow(workflow_id)
        if workflow:
            self._workflows[workflow_id] = workflow
        return workflow

    def update_product(
        self, workflow_id: str, product: ProductDescription
    ) -> SurveyWorkflow:
        """Update product description (Step 1).

        Allows going back to edit product before survey execution starts.
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Allow editing product in early stages (before survey execution)
        allowed_statuses = [
            WorkflowStatus.PRODUCT_INPUT,
            WorkflowStatus.PERSONA_BUILDING,
            WorkflowStatus.PERSONA_CONFIRMING,
            WorkflowStatus.SAMPLE_SIZE_SELECTION,
            WorkflowStatus.GENERATING_PERSONAS,
        ]
        if workflow.status not in allowed_statuses:
            raise ValueError(
                f"Cannot update product in status {workflow.status}. Survey already started."
            )

        workflow.product = product
        workflow.status = WorkflowStatus.PERSONA_BUILDING
        workflow.current_step = 2
        # Reset downstream data when going back
        workflow.persona_generation_job_id = None
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        self._save_to_database(workflow)
        return workflow

    def update_core_persona(
        self, workflow_id: str, core_persona: CorePersona
    ) -> SurveyWorkflow:
        """Update core persona (Step 2).

        Allows going back to edit persona before survey execution starts.
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Allow editing persona in early stages (before survey execution)
        allowed_statuses = [
            WorkflowStatus.PERSONA_BUILDING,
            WorkflowStatus.PERSONA_CONFIRMING,
            WorkflowStatus.SAMPLE_SIZE_SELECTION,
            WorkflowStatus.GENERATING_PERSONAS,
        ]
        if workflow.status not in allowed_statuses:
            raise ValueError(
                f"Cannot update persona in status {workflow.status}. Survey already started."
            )

        workflow.core_persona = core_persona
        workflow.status = WorkflowStatus.PERSONA_CONFIRMING
        workflow.current_step = 3
        # Reset downstream data when going back
        workflow.persona_generation_job_id = None
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        self._save_to_database(workflow)
        return workflow

    def confirm_persona(self, workflow_id: str) -> SurveyWorkflow:
        """Confirm core persona (Step 3).

        Allows re-confirming when going back from later steps.
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Allow confirming from various states (for back navigation)
        allowed_statuses = [
            WorkflowStatus.PERSONA_CONFIRMING,
            WorkflowStatus.SAMPLE_SIZE_SELECTION,
            WorkflowStatus.GENERATING_PERSONAS,
        ]
        if workflow.status not in allowed_statuses:
            raise ValueError(
                f"Cannot confirm persona in status {workflow.status}. Survey already started."
            )

        workflow.status = WorkflowStatus.SAMPLE_SIZE_SELECTION
        workflow.current_step = 4
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        self._save_to_database(workflow)
        return workflow

    def set_sample_size(self, workflow_id: str, sample_size: int) -> SurveyWorkflow:
        """Set sample size (Step 4).

        Allows changing sample size before survey execution.
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Allow setting sample size from various states (for back navigation)
        allowed_statuses = [
            WorkflowStatus.SAMPLE_SIZE_SELECTION,
            WorkflowStatus.GENERATING_PERSONAS,
        ]
        if workflow.status not in allowed_statuses:
            raise ValueError(
                f"Cannot set sample size in status {workflow.status}. Survey already started."
            )

        if not 100 <= sample_size <= 10000:
            raise ValueError("Sample size must be between 100 and 10000")

        workflow.sample_size = sample_size
        workflow.status = WorkflowStatus.GENERATING_PERSONAS
        workflow.current_step = 5
        # Reset generation job when changing sample size
        workflow.persona_generation_job_id = None
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        self._save_to_database(workflow)
        return workflow

    def update_concepts(
        self, workflow_id: str, concepts: list[ConceptInput]
    ) -> SurveyWorkflow:
        """Update concepts for comparison (Step 6).

        Allows setting 1-5 concepts for comparison after persona generation.
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Allow setting concepts after persona generation or when already in concepts step
        allowed_statuses = [
            WorkflowStatus.GENERATING_PERSONAS,
            WorkflowStatus.CONCEPTS_MANAGEMENT,
            WorkflowStatus.SURVEYING,
        ]
        if workflow.status not in allowed_statuses:
            raise ValueError(
                f"Cannot update concepts in status {workflow.status}. "
                "Complete persona generation first."
            )

        if not concepts or len(concepts) < 1:
            raise ValueError("At least 1 concept is required")
        if len(concepts) > 5:
            raise ValueError("Maximum 5 concepts allowed")

        workflow.concepts = concepts
        workflow.status = WorkflowStatus.CONCEPTS_MANAGEMENT
        workflow.current_step = 6
        # Reset survey execution when changing concepts
        workflow.survey_execution_job_id = None
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        self._save_to_database(workflow)
        return workflow

    def confirm_concepts(self, workflow_id: str) -> SurveyWorkflow:
        """Confirm concepts and proceed to survey execution (Step 6 → 7)."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if workflow.status != WorkflowStatus.CONCEPTS_MANAGEMENT:
            raise ValueError(
                f"Cannot confirm concepts in status {workflow.status}"
            )

        if not workflow.concepts:
            raise ValueError("No concepts to confirm. Add at least 1 concept.")

        workflow.status = WorkflowStatus.SURVEYING
        workflow.current_step = 7
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        self._save_to_database(workflow)
        return workflow

    def start_persona_generation(
        self, workflow_id: str, job_id: str
    ) -> SurveyWorkflow:
        """Mark persona generation started (Step 5)."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.persona_generation_job_id = job_id
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        self._save_to_database(workflow)
        return workflow

    def complete_persona_generation(self, workflow_id: str) -> SurveyWorkflow:
        """Mark persona generation completed."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Already completed or further along - idempotent behavior
        if workflow.status in (
            WorkflowStatus.SURVEYING,
            WorkflowStatus.COMPLETED,
        ):
            return workflow

        if workflow.status != WorkflowStatus.GENERATING_PERSONAS:
            raise ValueError(
                f"Cannot complete generation in status {workflow.status}"
            )

        workflow.status = WorkflowStatus.SURVEYING
        workflow.current_step = 6
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        self._save_to_database(workflow)
        return workflow

    def start_survey_execution(
        self, workflow_id: str, job_id: str
    ) -> SurveyWorkflow:
        """Mark survey execution started (Step 6)."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.survey_execution_job_id = job_id
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        self._save_to_database(workflow)
        return workflow

    def complete_survey(self, workflow_id: str) -> SurveyWorkflow:
        """Mark survey completed (Step 7)."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if workflow.status != WorkflowStatus.SURVEYING:
            raise ValueError(
                f"Cannot complete survey in status {workflow.status}"
            )

        workflow.status = WorkflowStatus.COMPLETED
        workflow.current_step = 7
        workflow.completed_at = datetime.now(timezone.utc)
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        self._save_to_database(workflow)
        return workflow

    def fail_workflow(self, workflow_id: str, error_message: str) -> SurveyWorkflow:
        """Mark workflow as failed."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.status = WorkflowStatus.FAILED
        workflow.error_message = error_message
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        self._save_to_database(workflow)
        return workflow

    def list_workflows(self) -> list[SurveyWorkflow]:
        """List all workflows."""
        # Refresh from database
        self._load_from_database()
        return list(self._workflows.values())


_workflow_service: Optional[WorkflowService] = None


def get_workflow_service() -> WorkflowService:
    """Get singleton workflow service."""
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = WorkflowService()
    return _workflow_service
