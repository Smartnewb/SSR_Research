"""Research API routes."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.models.research import (
    ResearchPromptRequest,
    ResearchPromptResponse,
    ParseReportRequest,
    ParseReportResponse,
    SaveCorePersonaRequest,
    SaveCorePersonaResponse,
    SegmentMarketRequest,
    SegmentMarketResponse,
    GeneratePersonasRequest as ArchetypeGenerateRequest,
    GeneratePersonasResponse as ArchetypeGenerateResponse,
    Archetype,
)
from backend.app.services.research import (
    generate_research_prompt,
    generate_research_prompt_mock,
    parse_research_report,
    parse_research_report_mock,
    segment_market_from_report,
)
from backend.app.services.persona_generation import (
    generate_synthetic_sample,
    calculate_distribution_stats,
    persona_to_system_prompt,
    distribute_samples_by_archetype,
    generate_enriched_personas_from_archetypes,
)

router = APIRouter(prefix="/api/research-legacy", tags=["research-legacy"])

personas_router = APIRouter(prefix="/api/personas", tags=["personas"])

_core_personas_store: dict[str, dict] = {}


@router.post("/generate-prompt", response_model=ResearchPromptResponse)
async def generate_prompt(request: ResearchPromptRequest, use_mock: bool = False):
    """Generate a research prompt for Gemini Deep Research.
    
    This endpoint creates a structured prompt that can be used with
    Gemini Deep Research to gather comprehensive consumer insights.
    """
    try:
        if use_mock:
            result = await generate_research_prompt_mock(
                product_category=request.product_category,
                target_description=request.target_description,
                market=request.market,
            )
        else:
            result = await generate_research_prompt(
                product_category=request.product_category,
                target_description=request.target_description,
                market=request.market,
            )
        return ResearchPromptResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-report", response_model=ParseReportResponse)
async def parse_report(request: ParseReportRequest, use_mock: bool = False):
    """Parse a Gemini research report and extract persona data.
    
    This endpoint analyzes a research report and extracts structured
    persona attributes including demographics, behavior, and preferences.
    """
    try:
        if use_mock:
            result = await parse_research_report_mock(request.research_report)
        else:
            result = await parse_research_report(request.research_report)
        return ParseReportResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@personas_router.post("/core", response_model=SaveCorePersonaResponse)
async def save_core_persona(request: SaveCorePersonaRequest):
    """Save a core persona profile.
    
    This stores the persona profile for later use in sample generation.
    """
    persona_id = f"PERSONA_CORE_{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()

    persona_data = {
        "id": persona_id,
        "name": request.name,
        "age_range": list(request.age_range),
        "gender_distribution": request.gender_distribution.model_dump(),
        "income_brackets": request.income_brackets.model_dump(),
        "location": request.location,
        "category_usage": request.category_usage,
        "shopping_behavior": request.shopping_behavior,
        "key_pain_points": request.key_pain_points,
        "decision_drivers": request.decision_drivers,
        "created_at": created_at,
        "status": "ready_for_generation",
    }

    _core_personas_store[persona_id] = persona_data

    return SaveCorePersonaResponse(
        id=persona_id,
        created_at=created_at,
        status="ready_for_generation",
    )


@personas_router.get("/core/{persona_id}")
async def get_core_persona(persona_id: str):
    """Get a saved core persona by ID."""
    if persona_id not in _core_personas_store:
        raise HTTPException(status_code=404, detail="Persona not found")
    return _core_personas_store[persona_id]


@personas_router.get("/core")
async def list_core_personas():
    """List all saved core personas."""
    return list(_core_personas_store.values())


# Generation models
class GeneratePersonasRequest(BaseModel):
    """Request model for generating synthetic personas."""

    core_persona_id: Optional[str] = Field(None, description="ID of saved core persona")
    core_config: Optional[dict] = Field(None, description="Direct core persona config (if no ID)")
    sample_size: int = Field(100, ge=5, le=10000, description="Number of personas to generate")
    random_seed: Optional[int] = Field(None, description="Random seed for reproducibility")


class GeneratePersonasResponse(BaseModel):
    """Response model for generated personas."""

    job_id: str
    total_personas: int
    distribution_stats: dict
    personas: list[dict]


@personas_router.post("/generate", response_model=GeneratePersonasResponse)
async def generate_personas(request: GeneratePersonasRequest):
    """Generate synthetic personas from a core persona profile.

    Generates N personas following the distribution defined in the core persona.
    Supports both ID-based lookup and direct config input.
    """
    # Get core config
    if request.core_persona_id:
        if request.core_persona_id not in _core_personas_store:
            raise HTTPException(status_code=404, detail="Core persona not found")
        core_config = _core_personas_store[request.core_persona_id]
    elif request.core_config:
        core_config = request.core_config
    else:
        raise HTTPException(
            status_code=400,
            detail="Either core_persona_id or core_config must be provided"
        )

    try:
        personas = generate_synthetic_sample(
            core_persona=core_config,
            sample_size=request.sample_size,
            random_seed=request.random_seed,
        )

        stats = calculate_distribution_stats(personas)

        job_id = f"JOB_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4].upper()}"

        return GeneratePersonasResponse(
            job_id=job_id,
            total_personas=len(personas),
            distribution_stats=stats.get("distribution_stats", {}),
            personas=personas,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@personas_router.get("/preview")
async def preview_personas(
    core_persona_id: Optional[str] = Query(None, description="Core persona ID"),
    count: int = Query(5, ge=1, le=20, description="Number of preview personas"),
):
    """Preview a small sample of generated personas.

    Use this to verify persona quality before generating a large sample.
    """
    if not core_persona_id:
        # Return mock preview
        mock_config = {
            "age_range": [30, 45],
            "gender_distribution": {"female": 60, "male": 40},
            "income_brackets": {"low": 20, "mid": 60, "high": 20},
            "location": "urban",
            "category_usage": "high",
            "shopping_behavior": "smart_shopper",
            "key_pain_points": ["High prices", "Unclear benefits"],
            "decision_drivers": ["Quality", "Value"],
        }
    else:
        if core_persona_id not in _core_personas_store:
            raise HTTPException(status_code=404, detail="Core persona not found")
        mock_config = _core_personas_store[core_persona_id]

    # Generate preview using synthetic sample with fixed seed
    preview = generate_synthetic_sample(mock_config, count, random_seed=42)

    # Add system prompts for preview
    for persona in preview:
        persona["system_prompt"] = persona_to_system_prompt(persona)

    return {"preview_personas": preview}


# =============================================================================
# Multi-Archetype Stratified Sampling Pipeline (v2.0)
# =============================================================================

archetype_router = APIRouter(prefix="/api/archetypes", tags=["archetypes"])

_archetypes_store: dict[str, list[dict]] = {}


@archetype_router.post("/segment", response_model=SegmentMarketResponse)
async def segment_market(request: SegmentMarketRequest):
    """
    Step 1: Market Segmentation (GPT-5.2, reasoning: high).

    Analyzes a Gemini Deep Research report and extracts 3-5 distinct
    market segments (archetypes) with share ratios.

    This endpoint uses high reasoning effort for deep analysis of the
    research report to identify heterogeneous customer groups.
    """
    try:
        result = await segment_market_from_report(
            research_report=request.research_report,
            product_category=request.product_category,
            target_segments=request.target_segments,
        )

        session_id = f"SEG_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4].upper()}"
        _archetypes_store[session_id] = result["archetypes"]

        return SegmentMarketResponse(
            archetypes=[Archetype(**arch) for arch in result["archetypes"]],
            total_share=result["total_share"],
            segment_count=result["segment_count"],
            warnings=result.get("warnings", []),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@archetype_router.post("/distribute")
async def distribute_samples(
    archetypes: list[Archetype],
    total_samples: int = Query(1000, ge=10, le=10000, description="Total samples (10-10000)"),
):
    """
    Step 2: Distribution Preview (Pure Python/NumPy).

    Calculates sample distribution across archetypes without LLM.
    Use this to preview how samples will be allocated before generation.

    Scale Strategy:
    - Debug: 10-30 (quick validation)
    - Pilot: 100-300 (trend analysis)
    - Standard: 1000 (statistically significant)
    - Massive: 10000+ (large-scale simulation)
    """
    try:
        archetypes_dict = [arch.model_dump() for arch in archetypes]
        distribution_plan = distribute_samples_by_archetype(archetypes_dict, total_samples)

        return {
            "total_samples": total_samples,
            "distribution_plan": distribution_plan,
            "segment_count": len(distribution_plan),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@archetype_router.post("/generate", response_model=ArchetypeGenerateResponse)
async def generate_from_archetypes(request: ArchetypeGenerateRequest):
    """
    Steps 2+3: Distribution + Enrichment Pipeline.

    Generates personas following archetype distributions and enriches them
    with LLM-generated narratives (GPT-5-mini, verbosity: high).

    Parameters:
    - archetypes: List of market segments from Step 1
    - total_samples: Number of personas to generate (10-10000)
    - product_context: Product/service context for enrichment
    - enrich: Enable LLM enrichment (default: True)
    - random_seed: For reproducibility

    Cost Estimation (with enrichment):
    - 100 samples: ~$0.20
    - 1000 samples: ~$2.00
    - 10000 samples: ~$20.00
    """
    try:
        archetypes_dict = [arch.model_dump() for arch in request.archetypes]

        result = generate_enriched_personas_from_archetypes(
            archetypes=archetypes_dict,
            total_samples=request.total_samples,
            product_context=request.product_context,
            currency=request.currency,
            enrich=request.enrich,
            random_seed=request.random_seed,
        )

        return ArchetypeGenerateResponse(
            personas=result["personas"],
            distribution_plan=result["distribution_plan"],
            stats=result["stats"],
            segment_stats=result["segment_stats"],
            total_count=result["total_count"],
            enriched=result["enriched"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@archetype_router.post("/full-pipeline")
async def run_full_pipeline(
    research_report: str = Body(..., min_length=100, description="Gemini Deep Research report"),
    product_category: Optional[str] = None,
    total_samples: int = Query(1000, ge=10, le=10000),
    enrich: bool = True,
    currency: str = "KRW",
):
    """
    Complete Multi-Archetype Stratified Sampling Pipeline.

    Runs all 3 steps in sequence:
    1. Segmentation (GPT-5.2, reasoning: high)
    2. Distribution (Pure Python)
    3. Enrichment (GPT-5-mini, verbosity: high)

    Use this for end-to-end persona generation from a research report.
    """
    try:
        # Step 1: Segment
        segmentation_result = await segment_market_from_report(
            research_report=research_report,
            product_category=product_category,
            target_segments=4,
        )

        # Steps 2+3: Distribute & Enrich
        generation_result = generate_enriched_personas_from_archetypes(
            archetypes=segmentation_result["archetypes"],
            total_samples=total_samples,
            product_context=product_category,
            currency=currency,
            enrich=enrich,
        )

        return {
            "pipeline_status": "completed",
            "segmentation": {
                "archetypes": segmentation_result["archetypes"],
                "segment_count": segmentation_result["segment_count"],
                "warnings": segmentation_result.get("warnings", []),
            },
            "generation": {
                "total_count": generation_result["total_count"],
                "distribution_plan": generation_result["distribution_plan"],
                "segment_stats": generation_result["segment_stats"],
                "enriched": generation_result["enriched"],
            },
            "personas": generation_result["personas"],
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
