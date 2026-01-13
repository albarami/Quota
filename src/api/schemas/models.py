"""
Pydantic schemas for API request/response validation.

These schemas define the data structures for all API endpoints.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================
# Enums
# ============================================

class TierStatusEnum(str, Enum):
    """Tier availability status."""
    OPEN = "OPEN"
    RATIONED = "RATIONED"
    LIMITED = "LIMITED"
    CLOSED = "CLOSED"


class AlertLevelEnum(str, Enum):
    """Dominance alert levels."""
    OK = "OK"
    WATCH = "WATCH"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RequestStatusEnum(str, Enum):
    """Request processing status."""
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    PARTIAL = "PARTIAL"
    QUEUED = "QUEUED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"


class DecisionEnum(str, Enum):
    """Decision outcomes."""
    APPROVED = "APPROVED"
    PARTIAL = "PARTIAL"
    QUEUED = "QUEUED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"


# ============================================
# Dashboard Schemas
# ============================================

class TierStatusSchema(BaseModel):
    """Tier status information."""
    tier_level: int
    tier_name: str
    status: TierStatusEnum
    capacity: int
    share_pct: Optional[float] = None


class DominanceAlertSchema(BaseModel):
    """Dominance alert information."""
    profession_id: int
    profession_name: str
    share_pct: float
    velocity: float
    alert_level: AlertLevelEnum
    is_blocking: bool


class DashboardResponse(BaseModel):
    """Dashboard data for a nationality."""
    nationality_id: int
    nationality_code: str
    nationality_name: str
    cap: int
    stock: int
    headroom: int
    utilization_pct: float
    tier_statuses: list[TierStatusSchema]
    dominance_alerts: list[DominanceAlertSchema]
    queue_counts: dict[int, int]  # tier -> count
    projected_outflow: int
    last_updated: datetime


class DashboardOverviewResponse(BaseModel):
    """Overview of all nationalities."""
    nationalities: list[DashboardResponse]
    total_restricted: int
    total_workers: int
    total_headroom: int


# ============================================
# Cap Management Schemas
# ============================================

class CapConfigSchema(BaseModel):
    """Cap configuration for a nationality."""
    nationality_id: int
    nationality_code: str
    year: int
    cap_limit: int
    previous_cap: Optional[int] = None
    set_by: Optional[str] = None
    set_date: Optional[date] = None


class CapRecommendationSchema(BaseModel):
    """AI-generated cap recommendation."""
    nationality_id: int
    nationality_code: str
    current_stock: int
    current_cap: Optional[int]
    conservative_cap: int
    moderate_cap: int
    flexible_cap: int
    recommended_cap: int
    recommendation_level: str
    rationale: str
    key_factors: list[str]
    risks: list[str]


class SetCapRequest(BaseModel):
    """Request to set a new cap."""
    cap_limit: int = Field(..., gt=0, description="New cap limit")
    notes: Optional[str] = Field(None, max_length=500)


class SetCapResponse(BaseModel):
    """Response after setting cap."""
    success: bool
    nationality_id: int
    year: int
    new_cap: int
    message: str


# ============================================
# Request Processing Schemas
# ============================================

class QuotaRequestCreate(BaseModel):
    """Create a new quota request."""
    establishment_id: int
    nationality_id: int
    profession_id: int
    requested_count: int = Field(..., gt=0, le=500)


class QuotaRequestResponse(BaseModel):
    """Quota request details."""
    id: int
    establishment_id: int
    nationality_id: int
    nationality_code: str
    profession_id: int
    profession_name: str
    requested_count: int
    approved_count: int
    status: RequestStatusEnum
    priority_score: int
    tier_at_submission: Optional[int]
    submitted_date: datetime
    decided_date: Optional[datetime]
    decision_reason: Optional[str]


class EligibilityCheckRequest(BaseModel):
    """Check eligibility before submitting."""
    nationality_id: int
    profession_id: int
    establishment_id: int
    requested_count: int


class EligibilityCheckResponse(BaseModel):
    """Eligibility check result."""
    is_eligible: bool
    tier_level: int
    tier_name: str
    tier_status: TierStatusEnum
    dominance_alert: Optional[AlertLevelEnum]
    estimated_outcome: DecisionEnum
    priority_score: int
    messages: list[str]


class DecisionResponse(BaseModel):
    """Decision result after processing."""
    request_id: int
    decision: DecisionEnum
    approved_count: int
    queued_count: int
    priority_score: int
    tier_level: int
    tier_status: TierStatusEnum
    dominance_alert: Optional[AlertLevelEnum]
    reason: str
    alternatives: list[str]


class DecisionExplanationResponse(BaseModel):
    """AI-generated decision explanation."""
    request_id: int
    decision: str
    summary: str
    detailed_explanation: str
    factors_considered: list[str]
    next_steps: list[str]


# ============================================
# Queue Schemas
# ============================================

class QueueEntrySchema(BaseModel):
    """Queue entry information."""
    queue_id: int
    request_id: int
    queue_position: int
    tier_at_submission: int
    queued_date: datetime
    expiry_date: date
    days_until_expiry: int
    needs_confirmation: bool
    is_confirmed: bool


class QueueStatusResponse(BaseModel):
    """Queue status for a nationality."""
    nationality_id: int
    nationality_code: str
    total_queued: int
    by_tier: dict[int, list[QueueEntrySchema]]


class WithdrawResponse(BaseModel):
    """Response after withdrawing from queue."""
    success: bool
    request_id: int
    message: str


class ConfirmResponse(BaseModel):
    """Response after confirming queue entry."""
    success: bool
    request_id: int
    message: str


# ============================================
# Alert Schemas
# ============================================

class AlertDetailSchema(BaseModel):
    """Detailed dominance alert."""
    id: int
    nationality_id: int
    nationality_code: str
    profession_id: int
    profession_name: str
    share_pct: float
    velocity: float
    alert_level: AlertLevelEnum
    total_in_profession: int
    nationality_count: int
    detected_date: datetime
    is_active: bool


class AlertsResponse(BaseModel):
    """All alerts for a nationality."""
    nationality_id: int
    nationality_code: str
    alerts: list[AlertDetailSchema]
    total_count: int


class CriticalAlertsResponse(BaseModel):
    """All critical alerts across nationalities."""
    alerts: list[AlertDetailSchema]
    total_count: int


# ============================================
# Common Schemas
# ============================================

class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool
    message: str
    data: Optional[Any] = None
