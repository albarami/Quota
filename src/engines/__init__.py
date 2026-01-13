"""
Business logic engines package.

This package contains the core engines for the quota system:
- TierDiscoveryEngine: Discovers demand patterns per nationality
- CapacityEngine: Calculates headroom and tier availability
- DominanceAlertEngine: Monitors nationality concentration
- RequestProcessor: Main decision engine
- QueueProcessor: Manages auto-queue processing
- AIRecommendationEngine: Azure OpenAI integration

Usage:
    from src.engines import (
        TierDiscoveryEngine,
        CapacityEngine,
        DominanceAlertEngine,
        RequestProcessor,
        QueueProcessor,
        AIRecommendationEngine,
    )
"""

from src.engines.tier_discovery import (
    TierDiscoveryEngine,
    TierInfo,
    TierDiscoveryResult,
)
from src.engines.capacity import (
    CapacityEngine,
    TierStatus,
    HeadroomResult,
    TierStatusResult,
    OutflowProjection,
)
from src.engines.dominance import (
    DominanceAlertEngine,
    DominanceCheckResult,
    VelocityResult,
)
from src.engines.request_processor import (
    RequestProcessor,
    Decision,
)
from src.engines.queue_processor import (
    QueueProcessor,
    QueueEntry,
    QueueProcessingResult,
)
from src.engines.ai_engine import (
    AIRecommendationEngine,
    CapRecommendation,
    DecisionExplanation,
)

__all__ = [
    # Tier Discovery
    "TierDiscoveryEngine",
    "TierInfo",
    "TierDiscoveryResult",
    # Capacity
    "CapacityEngine",
    "TierStatus",
    "HeadroomResult",
    "TierStatusResult",
    "OutflowProjection",
    # Dominance
    "DominanceAlertEngine",
    "DominanceCheckResult",
    "VelocityResult",
    # Request Processing
    "RequestProcessor",
    "Decision",
    # Queue Processing
    "QueueProcessor",
    "QueueEntry",
    "QueueProcessingResult",
    # AI
    "AIRecommendationEngine",
    "CapRecommendation",
    "DecisionExplanation",
]
