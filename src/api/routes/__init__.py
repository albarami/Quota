"""
API routes package.

Exports all route modules for inclusion in the main app.
"""

from src.api.routes import dashboard, caps, requests, queue, alerts

__all__ = ["dashboard", "caps", "requests", "queue", "alerts"]
