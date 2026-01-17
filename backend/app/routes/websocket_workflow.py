"""WebSocket endpoints for workflow progress tracking."""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..routes.generation import _generation_jobs
from ..routes.execution import _execution_jobs
from ..routes.qie import _qie_jobs

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/workflows/{workflow_id}/progress")
async def websocket_workflow_progress(websocket: WebSocket, workflow_id: str):
    """WebSocket endpoint for workflow progress updates.

    Streams real-time progress for:
    - Persona generation (Step 5)
    - Survey execution (Step 6-7)
    - QIE analysis (Step 8)

    Messages sent:
    - {"type": "generation_progress", "progress": 0.5, "status": "generating"}
    - {"type": "execution_progress", "progress": 0.5, "completed": 50, "total": 100}
    - {"type": "qie_progress", "progress": 0.5, "stage": "tier1_processing", "message": "..."}
    - {"type": "error", "error": "..."}
    """
    await websocket.accept()

    try:
        last_gen_progress = -1.0
        last_exec_progress = -1.0
        last_qie_progress = -1.0

        while True:
            # Generation progress (Step 5)
            for job_id, job_status in _generation_jobs.items():
                if job_status.workflow_id == workflow_id:
                    if job_status.progress != last_gen_progress:
                        await websocket.send_json(
                            {
                                "type": "generation_progress",
                                "progress": job_status.progress,
                                "status": job_status.status,
                                "completed": job_status.generated_count,
                                "total": job_status.total_personas,
                            }
                        )
                        last_gen_progress = job_status.progress

                    if job_status.status == "failed":
                        await websocket.send_json(
                            {
                                "type": "error",
                                "stage": "generation",
                                "error": job_status.error or "Unknown error",
                            }
                        )

            # Execution progress (Step 6-7)
            for job_id, job_status in _execution_jobs.items():
                if job_status.workflow_id == workflow_id:
                    if job_status.progress != last_exec_progress:
                        await websocket.send_json(
                            {
                                "type": "execution_progress",
                                "progress": job_status.progress,
                                "status": job_status.status,
                                "completed": job_status.completed_count,
                                "total": job_status.total_respondents,
                            }
                        )
                        last_exec_progress = job_status.progress

                    if job_status.status == "failed":
                        await websocket.send_json(
                            {
                                "type": "error",
                                "stage": "execution",
                                "error": job_status.error or "Unknown error",
                            }
                        )

            # QIE progress (Step 8)
            for job_id, job_data in _qie_jobs.items():
                if job_data.get("workflow_id") == workflow_id:
                    current_progress = job_data.get("progress", 0)
                    if current_progress != last_qie_progress:
                        await websocket.send_json(
                            {
                                "type": "qie_progress",
                                "progress": current_progress,
                                "status": job_data.get("status", "pending"),
                                "stage": job_data.get("current_stage", ""),
                                "message": job_data.get("message", ""),
                                "processed": job_data.get("processed_count", 0),
                                "total": job_data.get("total_responses", 0),
                            }
                        )
                        last_qie_progress = current_progress

                    if job_data.get("status") == "failed":
                        await websocket.send_json(
                            {
                                "type": "error",
                                "stage": "qie",
                                "error": job_data.get("error") or "Unknown error",
                            }
                        )

            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
                message = json.loads(data)

                if message.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                pass

    except WebSocketDisconnect:
        pass
