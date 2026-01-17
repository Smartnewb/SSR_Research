"""API route modules."""

from .surveys import router as surveys_router
from .health import router as health_router
from .websocket import router as websocket_router
from .research import router as research_router, personas_router, archetype_router
from .concepts import router as concepts_router
from .comparison import router as comparison_router
from .workflows import router as workflows_router
from .research_workflow import router as research_workflow_router
from .generation import router as generation_router
from .execution import router as execution_router
from .websocket_workflow import router as websocket_workflow_router
from .qie import router as qie_router

__all__ = [
    "surveys_router",
    "health_router",
    "websocket_router",
    "research_router",
    "personas_router",
    "archetype_router",
    "concepts_router",
    "comparison_router",
    "workflows_router",
    "research_workflow_router",
    "generation_router",
    "execution_router",
    "websocket_workflow_router",
    "qie_router",
]
