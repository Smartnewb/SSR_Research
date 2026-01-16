"""Multi-concept comparison API routes."""

import time
import uuid
from typing import List, Dict
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel

from ..models.comparison import MultiCompareRequest, MultiCompareResponse
from ..services.comparison import run_multi_concept_comparison

router = APIRouter(prefix="/api/surveys", tags=["comparison"])

# In-memory storage (replace with database in production)
_persona_sets_store: dict[str, list] = {}


@router.post("/multi-compare", response_model=MultiCompareResponse)
async def multi_concept_comparison(request: MultiCompareRequest):
    """
    Compare 2-5 product concepts side-by-side.

    This endpoint runs SSR surveys for multiple concepts using the same persona set,
    then compares results using:
    - Absolute SSR scores (mean, distribution)
    - Relative preference (pairwise comparison)
    - Statistical significance (t-test or ANOVA)
    - Segment analysis (winners by demographics)
    - LLM-extracted key differentiators

    Args:
        request: MultiCompareRequest with concepts, persona_set_id, sample_size

    Returns:
        MultiCompareResponse with comparison results

    Raises:
        HTTPException: 400 if persona set not found or insufficient size
        HTTPException: 500 if survey execution fails
    """
    start_time = time.time()

    try:
        # Load persona set
        personas = load_persona_set(request.persona_set_id)

        if len(personas) < request.sample_size:
            raise HTTPException(
                status_code=400,
                detail=f"Persona set '{request.persona_set_id}' has only {len(personas)} personas, "
                f"but {request.sample_size} requested. Generate more personas or reduce sample_size.",
            )

        # Sample personas
        sampled_personas = personas[: request.sample_size]

        # Run comparison
        results = await run_multi_concept_comparison(
            concepts=request.concepts,
            personas=sampled_personas,
            comparison_mode=request.comparison_mode,
            use_mock=request.use_mock,
        )

        execution_time = int((time.time() - start_time) * 1000)

        # Estimate cost (rough: $0.01 per persona per concept for GPT-4)
        total_cost = len(request.concepts) * request.sample_size * 0.01

        return MultiCompareResponse(
            comparison_id=f"CMP_{uuid.uuid4().hex[:12]}",
            results=results,
            execution_time_ms=execution_time,
            total_cost_usd=round(total_cost, 2),
            personas_tested=request.sample_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Multi-concept comparison failed: {str(e)}"
        )


def load_persona_set(persona_set_id: str) -> list:
    """
    Load persona set from storage.

    In production, this would query a database.
    For now, use in-memory store or load from file.
    """
    # Check in-memory store first
    if persona_set_id in _persona_sets_store:
        return _persona_sets_store[persona_set_id]

    # Try loading from file (for backward compatibility with Phase 4)
    import json
    from pathlib import Path

    # Look for persona JSON files
    project_root = Path(__file__).parent.parent.parent.parent
    persona_files = list(project_root.glob(f"generated_personas/{persona_set_id}*.json"))

    if not persona_files:
        # Try without generated_personas folder
        persona_files = list(project_root.glob(f"*{persona_set_id}*.json"))

    if not persona_files:
        raise HTTPException(
            status_code=404,
            detail=f"Persona set '{persona_set_id}' not found. "
            f"Generate personas first using /api/personas/generate",
        )

    # Load first matching file
    with open(persona_files[0], "r") as f:
        data = json.load(f)

    # Handle different JSON structures
    if isinstance(data, list):
        personas = data
    elif "personas" in data:
        personas = data["personas"]
    elif "generated_personas" in data:
        personas = data["generated_personas"]
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid persona file format for '{persona_set_id}'",
        )

    # Cache for future requests
    _persona_sets_store[persona_set_id] = personas

    return personas


class SavePersonaSetRequest(BaseModel):
    """Request for saving persona set."""
    persona_set_id: str
    personas: list[dict]


@router.post("/multi-compare/save-persona-set")
async def save_persona_set(request: SavePersonaSetRequest):
    """
    Save a persona set for later use in comparisons.

    This is a helper endpoint for testing and development.
    """
    _persona_sets_store[request.persona_set_id] = request.personas
    return {"persona_set_id": request.persona_set_id, "count": len(request.personas)}


@router.get("/multi-compare/persona-sets")
async def list_persona_sets():
    """List all available persona sets."""
    return {
        "persona_sets": [
            {"id": key, "count": len(value)}
            for key, value in _persona_sets_store.items()
        ]
    }
