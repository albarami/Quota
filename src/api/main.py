"""
FastAPI application entry point.

This module initializes the FastAPI application and includes all routes.

Usage:
    uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from src.models.base import init_database

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    print("Starting Nationality Quota System API...")
    init_database()
    print("Database initialized.")
    yield
    # Shutdown
    print("Shutting down API...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    Qatar Ministry of Labour - Nationality Quota Allocation System API
    
    A dynamic, demand-driven quota allocation system for restricted nationalities
    in Qatar's private sector.
    
    ## Features
    
    * **Dashboard**: Real-time monitoring of caps, headroom, and tier status
    * **Cap Management**: Set and manage nationality caps with AI recommendations
    * **Request Processing**: Submit and track quota requests
    * **Queue Management**: Auto-queue for requests waiting for capacity
    * **Dominance Alerts**: Monitor nationality concentration risks
    
    ## Authentication
    
    This API currently uses no authentication for demo purposes.
    Production deployment should implement proper authentication.
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import and include routers
from src.api.routes import dashboard, caps, requests, queue, alerts

app.include_router(
    dashboard.router,
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
)

app.include_router(
    caps.router,
    prefix="/api/v1/caps",
    tags=["Cap Management"],
)

app.include_router(
    requests.router,
    prefix="/api/v1/requests",
    tags=["Requests"],
)

app.include_router(
    queue.router,
    prefix="/api/v1/queue",
    tags=["Queue"],
)

app.include_router(
    alerts.router,
    prefix="/api/v1/alerts",
    tags=["Alerts"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "operational",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "version": settings.APP_VERSION,
    }
