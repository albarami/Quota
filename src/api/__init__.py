"""
API package.

FastAPI application with all routes and schemas.

Usage:
    uvicorn src.api.main:app --reload
"""

from src.api.main import app

__all__ = ["app"]
