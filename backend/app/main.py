"""FastAPI main application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .routes import surveys_router, health_router, websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="""
SSR Market Research API - Generate synthetic purchase intent data using
the Semantic Similarity Rating (SSR) method.

## Features
- Run surveys with synthetic personas
- A/B testing for product comparisons
- Demographic targeting
- Real-time progress tracking (WebSocket)

## Quick Start
1. Use mock mode for testing (no API key required)
2. Set OPENAI_API_KEY for live surveys
""",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(surveys_router)
app.include_router(websocket_router)
