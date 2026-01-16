"""Workflow API routes."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.workflow import (
    SurveyWorkflow,
    ProductDescriptionRequest,
    ProductDescriptionAssistRequest,
    CorePersonaRequest,
    SampleSizeRequest,
    ConceptsRequest,
    ProductDescription,
    CorePersona,
)
from ..models.comparison import ConceptInput
from ..services.workflow import get_workflow_service
from ..services.product import (
    assist_product_description,
    assist_product_description_mock,
)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


class CreateWorkflowResponse(BaseModel):
    """Response for workflow creation."""

    workflow_id: str
    status: str
    current_step: int


class ProductAssistResponse(BaseModel):
    """Response for product description assistance."""

    category: str
    description: str
    features: list[str]
    price_point: str
    target_market: str


@router.get("", response_model=list[SurveyWorkflow])
async def list_workflows():
    """List all workflows.

    Returns all workflows sorted by creation time (newest first).
    Useful for showing previous surveys and allowing users to reuse settings.
    """
    service = get_workflow_service()
    workflows = service.list_workflows()
    # Sort by creation time (newest first)
    workflows.sort(key=lambda w: w.id, reverse=True)
    return workflows


@router.post("", response_model=CreateWorkflowResponse)
async def create_workflow(copy_from: str = Query(None, description="Copy product and persona from existing workflow")):
    """Create a new survey workflow.

    This starts a new multi-step survey workflow.
    User will progress through 7 steps:
    1. Product Description
    2. Core Persona Building
    3. Confirm Persona
    4. Sample Size Selection
    5. Generate Persona Variations
    6. Execute Survey
    7. View Results

    If copy_from is provided, the product and persona will be copied from that workflow.
    """
    service = get_workflow_service()
    workflow = service.create_workflow()

    # Copy data from existing workflow if requested
    if copy_from:
        try:
            source_workflow = service.get_workflow(copy_from)
            if source_workflow.product:
                workflow.product = ProductDescription(**source_workflow.product.model_dump())
                workflow.current_step = 2
            if source_workflow.persona:
                workflow.persona = CorePersona(**source_workflow.persona.model_dump())
        except Exception:
            # If copy fails, just create empty workflow
            pass

    return CreateWorkflowResponse(
        workflow_id=workflow.id,
        status=workflow.status.value,
        current_step=workflow.current_step,
    )


@router.get("/{workflow_id}", response_model=SurveyWorkflow)
async def get_workflow(workflow_id: str):
    """Get workflow status and data."""
    service = get_workflow_service()
    workflow = service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow


@router.get("", response_model=list[SurveyWorkflow])
async def list_workflows():
    """List all workflows."""
    service = get_workflow_service()
    return service.list_workflows()


@router.post("/products/assist", response_model=ProductAssistResponse)
async def assist_product(
    request: ProductDescriptionAssistRequest, use_mock: bool = Query(False)
):
    """Get AI assistance for product description.

    This endpoint helps users create a comprehensive product description
    by providing suggestions based on basic product info.
    """
    try:
        if use_mock:
            result = await assist_product_description_mock(
                product_name=request.product_name,
                brief_description=request.brief_description,
                target_audience=request.target_audience,
            )
        else:
            result = await assist_product_description(
                product_name=request.product_name,
                brief_description=request.brief_description,
                target_audience=request.target_audience,
            )

        return ProductAssistResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/product", response_model=SurveyWorkflow)
async def update_product(workflow_id: str, request: ProductDescriptionRequest):
    """Update product description (Step 1).

    Saves the product description and advances to persona building.
    """
    service = get_workflow_service()

    try:
        product = ProductDescription(
            name=request.name,
            category=request.category,
            description=request.description,
            features=request.features,
            price_point=request.price_point,
            target_market=request.target_market,
        )

        workflow = service.update_product(workflow_id, product)
        return workflow

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/persona", response_model=SurveyWorkflow)
async def update_persona(workflow_id: str, request: CorePersonaRequest):
    """Update core persona (Step 2).

    Saves the 7-field core persona and advances to confirmation.
    """
    service = get_workflow_service()

    try:
        persona = CorePersona(
            age_range=request.age_range,
            gender_distribution=request.gender_distribution,
            income_brackets=request.income_brackets,
            location=request.location,
            category_usage=request.category_usage,
            shopping_behavior=request.shopping_behavior,
            key_pain_points=request.key_pain_points,
            decision_drivers=request.decision_drivers,
        )

        workflow = service.update_core_persona(workflow_id, persona)
        return workflow

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/confirm", response_model=SurveyWorkflow)
async def confirm_persona(workflow_id: str):
    """Confirm core persona (Step 3).

    User confirms the persona and advances to sample size selection.
    """
    service = get_workflow_service()

    try:
        workflow = service.confirm_persona(workflow_id)
        return workflow

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/sample-size", response_model=SurveyWorkflow)
async def set_sample_size(workflow_id: str, request: SampleSizeRequest):
    """Set sample size (Step 4).

    User selects how many synthetic personas to generate.
    Valid range: 100-10,000
    """
    service = get_workflow_service()

    try:
        workflow = service.set_sample_size(workflow_id, request.sample_size)
        return workflow

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/concepts", response_model=SurveyWorkflow)
async def update_concepts(workflow_id: str, request: ConceptsRequest):
    """Update concepts for comparison (Step 6).

    User can add 1-5 concepts to compare.
    - 1 concept: Single product survey
    - 2 concepts: A/B Testing with t-test
    - 3-5 concepts: Multi-concept comparison with ANOVA

    If no concepts are provided, the product from Step 1 is used as a single concept.
    """
    service = get_workflow_service()

    try:
        workflow = service.update_concepts(workflow_id, request.concepts)
        return workflow

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/concepts/from-product", response_model=SurveyWorkflow)
async def create_concept_from_product(workflow_id: str):
    """Create initial concept from product description.

    Converts the product from Step 1 into a concept for Step 6.
    This is called automatically when entering the concepts step.
    """
    service = get_workflow_service()

    try:
        workflow = service.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        if not workflow.product:
            raise HTTPException(status_code=400, detail="Product description not found")

        # Convert product to concept if no concepts exist
        if not workflow.concepts:
            concept = ConceptInput(
                id="CONCEPT_001",
                title=workflow.product.name,
                headline=workflow.product.description[:200] if len(workflow.product.description) > 200 else workflow.product.description,
                consumer_insight=f"Target market: {workflow.product.target_market}",
                benefit=", ".join(workflow.product.features[:3]) if workflow.product.features else "Key benefits",
                rtb=f"Category: {workflow.product.category}",
                image_description=f"Visual representation of {workflow.product.name}",
                price=workflow.product.price_point or "Contact for pricing",
            )
            workflow = service.update_concepts(workflow_id, [concept])

        return workflow

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
