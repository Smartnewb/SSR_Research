"""WebSocket endpoints for workflow progress tracking."""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..routes.generation import _generation_jobs
from ..routes.execution import _execution_jobs

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/workflows/{workflow_id}/progress")
async def websocket_workflow_progress(websocket: WebSocket, workflow_id: str):
    """WebSocket endpoint for workflow progress updates.

    Streams real-time progress for both persona generation (Step 5)
    and survey execution (Step 6).

    Messages sent:
    - {"type": "generation_progress", "progress": 0.5, "status": "generating"}
    - {"type": "execution_progress", "progress": 0.5, "completed": 50, "total": 100}
    - {"type": "error", "error": "..."}
    """
    await websocket.accept()

    try:
        last_gen_progress = -1.0
        last_exec_progress = -1.0

        while True:
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

            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
                message = json.loads(data)

                if message.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                pass

    except WebSocketDisconnect:
        pass
