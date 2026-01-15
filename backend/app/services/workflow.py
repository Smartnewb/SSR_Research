"""Survey workflow service."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from ..models.workflow import (
    SurveyWorkflow,
    WorkflowStatus,
    ProductDescription,
    CorePersona,
)


class WorkflowService:
    """Service for managing survey workflows."""

    def __init__(self):
        self._workflows: dict[str, SurveyWorkflow] = {}

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
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[SurveyWorkflow]:
        """Get workflow by ID."""
        return self._workflows.get(workflow_id)

    def update_product(
        self, workflow_id: str, product: ProductDescription
    ) -> SurveyWorkflow:
        """Update product description (Step 1)."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if workflow.status != WorkflowStatus.PRODUCT_INPUT:
            raise ValueError(
                f"Cannot update product in status {workflow.status}"
            )

        workflow.product = product
        workflow.status = WorkflowStatus.PERSONA_BUILDING
        workflow.current_step = 2
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        return workflow

    def update_core_persona(
        self, workflow_id: str, core_persona: CorePersona
    ) -> SurveyWorkflow:
        """Update core persona (Step 2).

        Allows updating from PERSONA_BUILDING or PERSONA_CONFIRMING status
        (when user clicks Edit and comes back to modify).
        """
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        allowed_statuses = [
            WorkflowStatus.PERSONA_BUILDING,
            WorkflowStatus.PERSONA_CONFIRMING,
        ]
        if workflow.status not in allowed_statuses:
            raise ValueError(
                f"Cannot update persona in status {workflow.status}"
            )

        workflow.core_persona = core_persona
        workflow.status = WorkflowStatus.PERSONA_CONFIRMING
        workflow.current_step = 3
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        return workflow

    def confirm_persona(self, workflow_id: str) -> SurveyWorkflow:
        """Confirm core persona (Step 3)."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if workflow.status != WorkflowStatus.PERSONA_CONFIRMING:
            raise ValueError(
                f"Cannot confirm persona in status {workflow.status}"
            )

        workflow.status = WorkflowStatus.SAMPLE_SIZE_SELECTION
        workflow.current_step = 4
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        return workflow

    def set_sample_size(self, workflow_id: str, sample_size: int) -> SurveyWorkflow:
        """Set sample size (Step 4)."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if workflow.status != WorkflowStatus.SAMPLE_SIZE_SELECTION:
            raise ValueError(
                f"Cannot set sample size in status {workflow.status}"
            )

        if not 100 <= sample_size <= 10000:
            raise ValueError("Sample size must be between 100 and 10000")

        workflow.sample_size = sample_size
        workflow.status = WorkflowStatus.GENERATING_PERSONAS
        workflow.current_step = 5
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        return workflow

    def start_persona_generation(
        self, workflow_id: str, job_id: str
    ) -> SurveyWorkflow:
        """Mark persona generation started (Step 5)."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.persona_generation_job_id = job_id
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        return workflow

    def complete_persona_generation(self, workflow_id: str) -> SurveyWorkflow:
        """Mark persona generation completed."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if workflow.status != WorkflowStatus.GENERATING_PERSONAS:
            raise ValueError(
                f"Cannot complete generation in status {workflow.status}"
            )

        workflow.status = WorkflowStatus.SURVEYING
        workflow.current_step = 6
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        return workflow

    def start_survey_execution(
        self, workflow_id: str, job_id: str
    ) -> SurveyWorkflow:
        """Mark survey execution started (Step 6)."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.survey_execution_job_id = job_id
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        return workflow

    def complete_survey(self, workflow_id: str) -> SurveyWorkflow:
        """Mark survey completed (Step 7)."""
        workflow = self._workflows.get(workflow_id)
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
        return workflow

    def fail_workflow(self, workflow_id: str, error_message: str) -> SurveyWorkflow:
        """Mark workflow as failed."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.status = WorkflowStatus.FAILED
        workflow.error_message = error_message
        workflow.updated_at = datetime.now(timezone.utc)

        self._workflows[workflow_id] = workflow
        return workflow

    def list_workflows(self) -> list[SurveyWorkflow]:
        """List all workflows."""
        return list(self._workflows.values())


_workflow_service = WorkflowService()


def get_workflow_service() -> WorkflowService:
    """Get singleton workflow service."""
    return _workflow_service
