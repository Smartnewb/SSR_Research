"""Concept API routes."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from backend.app.models.concept import (
    ConceptAssistRequest,
    ConceptAssistResponse,
    SuggestionItem,
    ConceptValidateRequest,
    ConceptValidateResponse,
    FieldFeedback,
    SaveConceptRequest,
    SaveConceptResponse,
)
from backend.app.services.concept import (
    assist_concept_field,
    assist_concept_field_mock,
    validate_concept,
    validate_concept_mock,
)

router = APIRouter(prefix="/api/concepts", tags=["concepts"])

_concepts_store: dict[str, dict] = {}


@router.post("/assist", response_model=ConceptAssistResponse)
async def assist_field(request: ConceptAssistRequest, use_mock: bool = False):
    """AI Writing Assistant for concept card fields.
    
    Provides 3 polished suggestions for any of the 7 concept card fields:
    - title: Product name
    - headline: One-sentence hook
    - insight: Consumer pain point
    - benefit: Core benefit/solution
    - rtb: Reason to Believe (technical credibility)
    - image_description: Product appearance
    - price: Pricing with context
    """
    try:
        if use_mock:
            suggestions = await assist_concept_field_mock(
                field=request.field,
                rough_idea=request.rough_idea,
                context=request.context,
            )
        else:
            suggestions = await assist_concept_field(
                field=request.field,
                rough_idea=request.rough_idea,
                context=request.context,
            )
        
        return ConceptAssistResponse(
            suggestions=[SuggestionItem(**s) for s in suggestions]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ConceptValidateResponse)
async def validate_concept_endpoint(request: ConceptValidateRequest, use_mock: bool = False):
    """Validate a product concept card.
    
    Returns a score (0-100), feedback for each field, and improvement suggestions.
    """
    try:
        concept_dict = request.model_dump()
        
        if use_mock:
            result = await validate_concept_mock(concept_dict)
        else:
            result = await validate_concept(concept_dict)
        
        feedback = {
            k: FieldFeedback(**v) 
            for k, v in result.get("feedback", {}).items()
        }
        
        return ConceptValidateResponse(
            is_valid=result.get("is_valid", True),
            score=result.get("score", 75),
            feedback=feedback,
            suggestions=result.get("suggestions", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=SaveConceptResponse)
async def save_concept(request: SaveConceptRequest, use_mock: bool = False):
    """Save a product concept card.
    
    Validates the concept and stores it for later use in surveys.
    """
    try:
        concept_dict = request.model_dump()
        
        if use_mock:
            validation = await validate_concept_mock(concept_dict)
        else:
            validation = await validate_concept(concept_dict)
        
        concept_id = f"CONCEPT_{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.now(timezone.utc).isoformat()
        
        concept_data = {
            "id": concept_id,
            **concept_dict,
            "validation_score": validation.get("score", 75),
            "created_at": created_at,
        }
        
        _concepts_store[concept_id] = concept_data
        
        return SaveConceptResponse(
            id=concept_id,
            validation_score=validation.get("score", 75),
            created_at=created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{concept_id}")
async def get_concept(concept_id: str):
    """Get a saved concept by ID."""
    if concept_id not in _concepts_store:
        raise HTTPException(status_code=404, detail="Concept not found")
    return _concepts_store[concept_id]


@router.get("")
async def list_concepts():
    """List all saved concepts."""
    return list(_concepts_store.values())
