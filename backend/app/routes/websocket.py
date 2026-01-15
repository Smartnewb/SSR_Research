"""WebSocket endpoints for real-time progress tracking."""

import asyncio
import json
import uuid
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..models.request import SurveyRequest
from ..models.response import SurveyStatusEnum
from ..services.survey import SurveyService

router = APIRouter(tags=["websocket"])

active_connections: Dict[str, WebSocket] = {}


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, survey_id: str):
        """Accept and store WebSocket connection."""
        await websocket.accept()
        self.active_connections[survey_id] = websocket

    def disconnect(self, survey_id: str):
        """Remove WebSocket connection."""
        if survey_id in self.active_connections:
            del self.active_connections[survey_id]

    async def send_progress(
        self,
        survey_id: str,
        status: str,
        progress: float,
        current_persona: int = 0,
        total_personas: int = 0,
        message: str = "",
    ):
        """Send progress update to client."""
        if survey_id in self.active_connections:
            websocket = self.active_connections[survey_id]
            await websocket.send_json({
                "type": "progress",
                "survey_id": survey_id,
                "status": status,
                "progress": progress,
                "current_persona": current_persona,
                "total_personas": total_personas,
                "message": message,
            })

    async def send_result(self, survey_id: str, result: dict):
        """Send final result to client."""
        if survey_id in self.active_connections:
            websocket = self.active_connections[survey_id]
            await websocket.send_json({
                "type": "result",
                "survey_id": survey_id,
                "data": result,
            })

    async def send_error(self, survey_id: str, error: str):
        """Send error to client."""
        if survey_id in self.active_connections:
            websocket = self.active_connections[survey_id]
            await websocket.send_json({
                "type": "error",
                "survey_id": survey_id,
                "error": error,
            })


manager = ConnectionManager()


@router.websocket("/ws/surveys/{survey_id}")
async def websocket_survey(websocket: WebSocket, survey_id: str):
    """
    WebSocket endpoint for real-time survey progress.

    Connect to this endpoint before starting a survey to receive
    live progress updates.

    Messages sent:
    - {"type": "progress", "progress": 50, "current_persona": 10, "total_personas": 20}
    - {"type": "result", "data": {...}}
    - {"type": "error", "error": "..."}
    """
    await manager.connect(websocket, survey_id)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("action") == "start":
                request_data = message.get("request", {})

                try:
                    request = SurveyRequest(**request_data)
                    service = SurveyService(llm_model=request.model)

                    total = request.sample_size

                    def progress_callback(current: int, total: int):
                        asyncio.create_task(
                            manager.send_progress(
                                survey_id=survey_id,
                                status=SurveyStatusEnum.RUNNING,
                                progress=(current / total) * 100,
                                current_persona=current,
                                total_personas=total,
                                message=f"Processing persona {current}/{total}",
                            )
                        )

                    await manager.send_progress(
                        survey_id=survey_id,
                        status=SurveyStatusEnum.RUNNING,
                        progress=0,
                        current_persona=0,
                        total_personas=total,
                        message="Starting survey...",
                    )

                    result = await asyncio.to_thread(
                        service.run_survey,
                        request,
                        progress_callback,
                    )

                    await manager.send_result(
                        survey_id=survey_id,
                        result=result.model_dump(mode="json"),
                    )

                except Exception as e:
                    await manager.send_error(survey_id, str(e))

            elif message.get("action") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(survey_id)
