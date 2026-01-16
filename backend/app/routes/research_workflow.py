"""Research workflow API routes."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.gemini_research import (
    generate_gemini_research_prompt,
    generate_gemini_research_prompt_mock,
    parse_gemini_research_report,
    parse_gemini_research_report_mock,
)

router = APIRouter(prefix="/api/research", tags=["research"])


class GenerateResearchPromptRequest(BaseModel):
    """Request for generating Gemini research prompt."""

    product_category: str = Field(..., min_length=1)
    product_description: str = Field(..., min_length=1)
    product_name: str = Field(default="")
    target_market: str = Field(default="")
    price_point: str = Field(default="")
    initial_persona_draft: dict | None = Field(
        default=None, description="Optional initial draft of 7-field persona"
    )


class GenerateResearchPromptResponse(BaseModel):
    """Response for research prompt generation."""

    research_prompt: str
    research_objectives: list[str]


class ParseResearchReportRequest(BaseModel):
    """Request for parsing Gemini research report."""

    research_report: str = Field(..., min_length=100)


class ParseResearchReportResponse(BaseModel):
    """Response for parsed research report."""

    refined_demographics: dict
    behavioral_insights: dict
    psychographics: dict
    market_insights: dict
    confidence_score: float
    key_findings: list[str]


@router.post("/generate-prompt", response_model=GenerateResearchPromptResponse)
async def generate_research_prompt(
    request: GenerateResearchPromptRequest, use_mock: bool = Query(False)
):
    """Generate a research prompt for Gemini Deep Research.

    This endpoint creates a comprehensive research prompt based on:
    - Product information (name, category, description, price, target market)
    - Optional initial persona draft (7 fields)

    The prompt focuses on industry and market research to build an accurate
    target persona from scratch. User can copy this prompt and use it with
    Gemini Deep Research, then return the results for parsing.
    """
    try:
        if use_mock:
            result = await generate_gemini_research_prompt_mock(
                product_category=request.product_category,
                product_description=request.product_description,
                product_name=request.product_name,
                target_market=request.target_market,
                price_point=request.price_point,
                initial_persona_draft=request.initial_persona_draft,
            )
        else:
            result = await generate_gemini_research_prompt(
                product_category=request.product_category,
                product_description=request.product_description,
                product_name=request.product_name,
                target_market=request.target_market,
                price_point=request.price_point,
                initial_persona_draft=request.initial_persona_draft,
            )

        return GenerateResearchPromptResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-report", response_model=ParseResearchReportResponse)
async def parse_research_report(
    request: ParseResearchReportRequest, use_mock: bool = Query(False)
):
    """Parse Gemini Deep Research report and extract persona insights.

    This endpoint analyzes the research report from Gemini and extracts:
    - Refined demographics
    - Behavioral insights
    - Psychographics
    - Market insights
    - Confidence score and key findings

    These insights can be used to improve the core persona accuracy.
    """
    try:
        if use_mock:
            result = await parse_gemini_research_report_mock(
                research_report=request.research_report
            )
        else:
            result = await parse_gemini_research_report(
                research_report=request.research_report
            )

        return ParseResearchReportResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
