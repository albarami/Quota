"""
Database models package.

This package contains all SQLAlchemy models for the quota system.

Usage:
    from src.models import (
        Nationality, Profession, EconomicActivity, Establishment,
        NationalityCap, NationalityTier, DominanceAlert,
        WorkerStock, WorkerState,
        QuotaRequest, RequestQueue, DecisionLog,
        ParameterRegistry,
    )
"""

# Base classes and utilities
from src.models.base import Base, BaseModel, get_db, init_database, engine, SessionLocal

# Core entities
from src.models.core import (
    Nationality,
    Profession,
    EconomicActivity,
    Establishment,
)

# Quota management
from src.models.quota import (
    NationalityCap,
    NationalityTier,
    DominanceAlert,
    TierLevel,
    TierStatus,
    AlertLevel,
)

# Worker tracking
from src.models.worker import (
    WorkerStock,
    WorkerState,
)

# Request processing
from src.models.request import (
    QuotaRequest,
    RequestQueue,
    DecisionLog,
    RequestStatus,
    DecisionType,
)

# Configuration
from src.models.config import (
    ParameterRegistry,
    DEFAULT_PARAMETERS,
)

__all__ = [
    # Base
    "Base",
    "BaseModel",
    "get_db",
    "init_database",
    "engine",
    "SessionLocal",
    # Core entities
    "Nationality",
    "Profession",
    "EconomicActivity",
    "Establishment",
    # Quota management
    "NationalityCap",
    "NationalityTier",
    "DominanceAlert",
    "TierLevel",
    "TierStatus",
    "AlertLevel",
    # Worker tracking
    "WorkerStock",
    "WorkerState",
    # Request processing
    "QuotaRequest",
    "RequestQueue",
    "DecisionLog",
    "RequestStatus",
    "DecisionType",
    # Configuration
    "ParameterRegistry",
    "DEFAULT_PARAMETERS",
]
