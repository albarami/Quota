"""
Request processing models.

This module defines request-related entities:
- RequestStatus: Enum for request states
- DecisionType: Enum for decision outcomes
- QuotaRequest: Quota request records
- RequestQueue: Auto-queue entries
- DecisionLog: Audit trail for all decisions

These models implement the request flow from the technical specification.
"""

import enum
import json
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class RequestStatus(enum.Enum):
    """
    Request processing status.
    
    Tracks the lifecycle of a quota request.
    """
    
    SUBMITTED = "SUBMITTED"      # Initial submission
    PROCESSING = "PROCESSING"    # Under evaluation
    APPROVED = "APPROVED"        # Fully approved
    PARTIAL = "PARTIAL"          # Partially approved
    QUEUED = "QUEUED"            # Added to queue
    BLOCKED = "BLOCKED"          # Blocked (dominance)
    REJECTED = "REJECTED"        # Rejected
    WITHDRAWN = "WITHDRAWN"      # Withdrawn by applicant
    EXPIRED = "EXPIRED"          # Queue entry expired


class DecisionType(enum.Enum):
    """
    Decision outcome types.
    
    From technical specification Section 6.1.
    """
    
    APPROVED = "APPROVED"        # Full approval
    PARTIAL = "PARTIAL"          # Partial approval (limited capacity)
    QUEUED = "QUEUED"            # Added to auto-queue
    BLOCKED = "BLOCKED"          # Blocked due to dominance
    REJECTED = "REJECTED"        # Rejected (various reasons)


class QuotaRequest(BaseModel):
    """
    Quota request record.
    
    Represents a request from an establishment to hire workers
    of a specific nationality and profession.
    
    Attributes:
        establishment_id: Foreign key to requesting establishment.
        nationality_id: Foreign key to requested nationality.
        profession_id: Foreign key to requested profession.
        requested_count: Number of workers requested.
        approved_count: Number actually approved.
        status: Current request status.
        priority_score: Calculated priority score.
        tier_at_submission: Tier level when request was submitted.
        submitted_date: When request was submitted.
        decided_date: When decision was made.
        decision_reason: Human-readable decision explanation.
        ai_explanation: AI-generated explanation (if applicable).
    """
    
    __tablename__ = "quota_request"
    
    establishment_id = Column(
        Integer,
        ForeignKey("establishment.id"),
        nullable=False,
        index=True,
        doc="Foreign key to requesting establishment"
    )
    nationality_id = Column(
        Integer,
        ForeignKey("nationality.id"),
        nullable=False,
        index=True,
        doc="Foreign key to requested nationality"
    )
    profession_id = Column(
        Integer,
        ForeignKey("profession.id"),
        nullable=False,
        index=True,
        doc="Foreign key to requested profession"
    )
    requested_count = Column(
        Integer,
        nullable=False,
        doc="Number of workers requested"
    )
    approved_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number actually approved"
    )
    status = Column(
        Enum(RequestStatus),
        default=RequestStatus.SUBMITTED,
        nullable=False,
        index=True,
        doc="Current request status"
    )
    priority_score = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Calculated priority score"
    )
    tier_at_submission = Column(
        Integer,
        nullable=True,
        doc="Tier level when request was submitted"
    )
    submitted_date = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        doc="When request was submitted"
    )
    decided_date = Column(
        DateTime,
        nullable=True,
        doc="When decision was made"
    )
    decision_reason = Column(
        Text,
        nullable=True,
        doc="Human-readable decision explanation"
    )
    ai_explanation = Column(
        Text,
        nullable=True,
        doc="AI-generated explanation"
    )
    
    # Relationships
    establishment = relationship("Establishment", back_populates="requests")
    nationality = relationship("Nationality", back_populates="requests")
    profession = relationship("Profession", back_populates="requests")
    queue_entry = relationship("RequestQueue", back_populates="request", uselist=False)
    decision_logs = relationship("DecisionLog", back_populates="request")
    
    @property
    def is_pending(self) -> bool:
        """Check if request is still pending."""
        return self.status in [RequestStatus.SUBMITTED, RequestStatus.PROCESSING]
    
    @property
    def is_decided(self) -> bool:
        """Check if request has been decided."""
        return self.status not in [RequestStatus.SUBMITTED, RequestStatus.PROCESSING]
    
    @property
    def is_successful(self) -> bool:
        """Check if request was approved (fully or partially)."""
        return self.status in [RequestStatus.APPROVED, RequestStatus.PARTIAL]
    
    @property
    def approval_rate(self) -> float:
        """Calculate approval rate for this request."""
        if self.requested_count == 0:
            return 0.0
        return self.approved_count / self.requested_count
    
    def __repr__(self) -> str:
        return f"<QuotaRequest(id={self.id}, status={self.status.value}, count={self.requested_count})>"


class RequestQueue(BaseModel):
    """
    Auto-queue entry for requests waiting for capacity.
    
    When a tier is closed, requests can join the queue and be
    automatically processed when capacity opens.
    
    Attributes:
        request_id: Foreign key to quota request.
        queue_position: Position in queue (1 = first).
        tier_at_submission: Tier level when queued.
        queued_date: When added to queue.
        expiry_date: When queue entry expires (90 days).
        last_revalidation: When eligibility was last checked.
        confirmation_sent: Whether 30-day confirmation was sent.
        confirmed_date: When applicant confirmed interest.
        processing_priority: Priority for processing (higher = first).
    """
    
    __tablename__ = "request_queue"
    
    request_id = Column(
        Integer,
        ForeignKey("quota_request.id"),
        nullable=False,
        unique=True,
        index=True,
        doc="Foreign key to quota request"
    )
    queue_position = Column(
        Integer,
        nullable=False,
        doc="Position in queue"
    )
    tier_at_submission = Column(
        Integer,
        nullable=False,
        doc="Tier level when queued"
    )
    queued_date = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="When added to queue"
    )
    expiry_date = Column(
        Date,
        nullable=False,
        doc="When queue entry expires"
    )
    last_revalidation = Column(
        DateTime,
        nullable=True,
        doc="When eligibility was last checked"
    )
    confirmation_sent = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Whether 30-day confirmation was sent"
    )
    confirmed_date = Column(
        DateTime,
        nullable=True,
        doc="When applicant confirmed interest"
    )
    processing_priority = Column(
        Float,
        default=0.0,
        nullable=False,
        doc="Priority for processing"
    )
    
    # Relationships
    request = relationship("QuotaRequest", back_populates="queue_entry")
    
    @property
    def days_until_expiry(self) -> int:
        """Calculate days until queue entry expires."""
        delta = self.expiry_date - date.today()
        return delta.days
    
    @property
    def is_expired(self) -> bool:
        """Check if queue entry has expired."""
        return self.expiry_date < date.today()
    
    @property
    def needs_confirmation(self) -> bool:
        """Check if 30-day confirmation is needed."""
        if self.confirmation_sent:
            return False
        days_queued = (datetime.utcnow() - self.queued_date).days
        return days_queued >= 25  # Send at day 25, due at day 30
    
    def __repr__(self) -> str:
        return f"<RequestQueue(position={self.queue_position}, expires={self.expiry_date})>"


class DecisionLog(BaseModel):
    """
    Decision audit log for full explainability.
    
    Every decision is logged with complete context for audit,
    dispute resolution, and system improvement.
    
    Attributes:
        request_id: Foreign key to quota request.
        decision: Decision outcome.
        tier_status_snapshot: Tier statuses at decision time (JSON).
        capacity_snapshot: Capacity values at decision time (JSON).
        dominance_snapshot: Dominance data at decision time (JSON).
        priority_score: Calculated priority score.
        rule_chain: Sequence of rules evaluated (JSON).
        parameter_version: Version of parameter registry used.
        override_flag: Whether this was a manual override.
        override_authority: Who authorized override.
        override_reason: Why override was applied.
        decision_timestamp: When decision was made.
    """
    
    __tablename__ = "decision_log"
    
    request_id = Column(
        Integer,
        ForeignKey("quota_request.id"),
        nullable=False,
        index=True,
        doc="Foreign key to quota request"
    )
    decision = Column(
        Enum(DecisionType),
        nullable=False,
        index=True,
        doc="Decision outcome"
    )
    tier_status_snapshot = Column(
        Text,
        nullable=True,
        doc="Tier statuses at decision time (JSON)"
    )
    capacity_snapshot = Column(
        Text,
        nullable=True,
        doc="Capacity values at decision time (JSON)"
    )
    dominance_snapshot = Column(
        Text,
        nullable=True,
        doc="Dominance data at decision time (JSON)"
    )
    priority_score = Column(
        Integer,
        nullable=True,
        doc="Calculated priority score"
    )
    rule_chain = Column(
        Text,
        nullable=True,
        doc="Sequence of rules evaluated (JSON)"
    )
    parameter_version = Column(
        String(50),
        nullable=True,
        doc="Version of parameter registry used"
    )
    override_flag = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Whether this was a manual override"
    )
    override_authority = Column(
        String(100),
        nullable=True,
        doc="Who authorized override"
    )
    override_reason = Column(
        Text,
        nullable=True,
        doc="Why override was applied"
    )
    decision_timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        doc="When decision was made"
    )
    
    # Relationships
    request = relationship("QuotaRequest", back_populates="decision_logs")
    
    def get_tier_status(self) -> dict[str, Any]:
        """Parse tier status snapshot from JSON."""
        if self.tier_status_snapshot:
            return json.loads(self.tier_status_snapshot)
        return {}
    
    def get_capacity(self) -> dict[str, Any]:
        """Parse capacity snapshot from JSON."""
        if self.capacity_snapshot:
            return json.loads(self.capacity_snapshot)
        return {}
    
    def get_dominance(self) -> dict[str, Any]:
        """Parse dominance snapshot from JSON."""
        if self.dominance_snapshot:
            return json.loads(self.dominance_snapshot)
        return {}
    
    def get_rule_chain(self) -> list[dict[str, Any]]:
        """Parse rule chain from JSON."""
        if self.rule_chain:
            return json.loads(self.rule_chain)
        return []
    
    @property
    def is_override(self) -> bool:
        """Check if this was a manual override."""
        return bool(self.override_flag)
    
    def __repr__(self) -> str:
        return f"<DecisionLog(decision={self.decision.value}, override={self.is_override})>"
