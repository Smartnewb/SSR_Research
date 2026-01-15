"""Survey API endpoints."""

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from ..models.request import SurveyRequest, ABTestRequest
from ..models.response import SurveyResponse, ABTestResponse, ErrorResponse
from ..services.survey import SurveyService

router = APIRouter(prefix="/api/surveys", tags=["surveys"])


@router.post(
    "",
    response_model=SurveyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Survey execution failed"},
    },
)
async def run_survey(request: SurveyRequest) -> SurveyResponse:
    """
    Run a survey for a product concept.

    This endpoint generates synthetic personas and collects their opinions
    about the product, returning SSR scores and response texts.
    """
    try:
        service = SurveyService(llm_model=request.model)
        result = await asyncio.to_thread(service.run_survey, request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Survey execution failed: {e}")


@router.post(
    "/compare",
    response_model=ABTestResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "A/B test execution failed"},
    },
)
async def run_ab_test(request: ABTestRequest) -> ABTestResponse:
    """
    Run an A/B test comparing two product concepts.

    This endpoint runs surveys for both products using the same
    demographics and returns statistical comparison results.
    """
    try:
        service = SurveyService(llm_model=request.model)
        result = await asyncio.to_thread(service.run_ab_test, request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"A/B test execution failed: {e}")


@router.get(
    "/{survey_id}/export",
    response_class=StreamingResponse,
)
async def export_survey_csv(survey_id: str):
    """
    Export survey results as CSV.

    Note: In a full implementation, this would fetch results from a database.
    Currently returns a placeholder since we don't persist results.
    """
    raise HTTPException(
        status_code=501,
        detail="Survey persistence not implemented. Export from the response directly.",
    )
