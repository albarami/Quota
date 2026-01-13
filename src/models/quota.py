"""
Quota management models.

This module defines quota-related entities:
- NationalityCap: Annual caps set by policymakers
- NationalityTier: Discovered tier classifications
- DominanceAlert: Nationality concentration alerts

These models implement the core quota management logic from the technical specification.
"""

import enum
from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class TierLevel(enum.IntEnum):
    """
    Tier classification levels.
    
    Tiers are assigned based on percentage of requests for a nationality.
    Higher tiers are protected first when capacity is limited.
    """
    
    TIER_1 = 1  # Primary: >15% of requests
    TIER_2 = 2  # Secondary: 5-15% of requests
    TIER_3 = 3  # Minor: 1-5% of requests
    TIER_4 = 4  # Unusual: <1% of requests


class TierStatus(enum.Enum):
    """
    Tier availability status.
    
    Determined by available headroom relative to tier demand.
    """
    
    OPEN = "OPEN"          # Full capacity available
    RATIONED = "RATIONED"  # Limited capacity, priority scoring applies
    LIMITED = "LIMITED"    # Very limited capacity
    CLOSED = "CLOSED"      # No capacity available


class AlertLevel(enum.Enum):
    """
    Dominance alert severity levels.
    
    Based on nationality share in a profession and velocity of change.
    """
    
    OK = "OK"              # <30% share, normal processing
    WATCH = "WATCH"        # 30-40% share, flag for review
    HIGH = "HIGH"          # 40-50% share, partial approve only
    CRITICAL = "CRITICAL"  # >50% share, block new approvals


class NationalityCap(BaseModel):
    """
    Nationality cap configuration set by policymakers.
    
    Stores the annual cap limits for each restricted nationality.
    Policymakers set these based on system recommendations.
    
    Attributes:
        nationality_id: Foreign key to nationality.
        year: Year the cap applies to.
        cap_limit: Maximum workers allowed.
        previous_cap: Previous year's cap for comparison.
        set_by: Who set this cap.
        set_date: When the cap was set.
        notes: Additional notes or rationale.
    """
    
    __tablename__ = "nationality_cap"
    __table_args__ = (
        UniqueConstraint("nationality_id", "year", name="uq_nationality_year"),
    )
    
    nationality_id = Column(
        Integer,
        ForeignKey("nationality.id"),
        nullable=False,
        index=True,
        doc="Foreign key to nationality"
    )
    year = Column(
        Integer,
        nullable=False,
        index=True,
        doc="Year the cap applies to"
    )
    cap_limit = Column(
        Integer,
        nullable=False,
        doc="Maximum workers allowed"
    )
    previous_cap = Column(
        Integer,
        nullable=True,
        doc="Previous year's cap for comparison"
    )
    set_by = Column(
        String(100),
        nullable=True,
        doc="Who set this cap"
    )
    set_date = Column(
        Date,
        default=date.today,
        nullable=False,
        doc="When the cap was set"
    )
    notes = Column(
        String(500),
        nullable=True,
        doc="Additional notes or rationale"
    )
    
    # Relationships
    nationality = relationship("Nationality", back_populates="caps")
    
    @property
    def growth_rate(self) -> float | None:
        """
        Calculate growth rate from previous cap.
        
        Returns:
            float: Growth rate as decimal, or None if no previous cap.
        """
        if self.previous_cap is None or self.previous_cap == 0:
            return None
        return (self.cap_limit - self.previous_cap) / self.previous_cap
    
    def __repr__(self) -> str:
        return f"<NationalityCap(year={self.year}, limit={self.cap_limit})>"


class NationalityTier(BaseModel):
    """
    Tier classification for nationality-profession pairs.
    
    Stores the discovered tier assignments based on historical
    request patterns. Updated periodically by TierDiscoveryEngine.
    
    Attributes:
        nationality_id: Foreign key to nationality.
        profession_id: Foreign key to profession.
        tier_level: Tier classification (1-4).
        share_pct: Percentage of requests for this profession.
        request_count: Number of requests in calculation period.
        calculated_date: When this tier was calculated.
        valid_from: Start of validity period.
        valid_to: End of validity period (null if current).
    """
    
    __tablename__ = "nationality_tier"
    __table_args__ = (
        UniqueConstraint(
            "nationality_id", "profession_id", "valid_to",
            name="uq_nationality_profession_valid"
        ),
    )
    
    nationality_id = Column(
        Integer,
        ForeignKey("nationality.id"),
        nullable=False,
        index=True,
        doc="Foreign key to nationality"
    )
    profession_id = Column(
        Integer,
        ForeignKey("profession.id"),
        nullable=False,
        index=True,
        doc="Foreign key to profession"
    )
    tier_level = Column(
        Integer,
        nullable=False,
        index=True,
        doc="Tier classification (1=Primary, 2=Secondary, 3=Minor, 4=Unusual)"
    )
    share_pct = Column(
        Float,
        nullable=False,
        doc="Percentage of requests for this profession"
    )
    request_count = Column(
        Integer,
        nullable=True,
        doc="Number of requests in calculation period"
    )
    calculated_date = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="When this tier was calculated"
    )
    valid_from = Column(
        Date,
        default=date.today,
        nullable=False,
        doc="Start of validity period"
    )
    valid_to = Column(
        Date,
        nullable=True,
        doc="End of validity period (null if current)"
    )
    
    # Relationships
    nationality = relationship("Nationality", back_populates="tiers")
    profession = relationship("Profession", back_populates="tiers")
    
    @property
    def tier_name(self) -> str:
        """
        Get human-readable tier name.
        
        Returns:
            str: Tier name (Primary, Secondary, Minor, Unusual).
        """
        names = {1: "Primary", 2: "Secondary", 3: "Minor", 4: "Unusual"}
        return names.get(self.tier_level, "Unknown")
    
    @property
    def is_current(self) -> bool:
        """
        Check if this tier assignment is currently valid.
        
        Returns:
            bool: True if valid_to is None or in the future.
        """
        return self.valid_to is None or self.valid_to >= date.today()
    
    def __repr__(self) -> str:
        return f"<NationalityTier(tier={self.tier_level}, share={self.share_pct:.1%})>"


class DominanceAlert(BaseModel):
    """
    Dominance alert for nationality concentration in a profession.
    
    Monitors when a nationality's share in a profession becomes
    too high, creating concentration risk.
    
    Attributes:
        nationality_id: Foreign key to nationality.
        profession_id: Foreign key to profession.
        share_pct: Current nationality share in profession.
        velocity: Rate of share change (pp per 3 years).
        alert_level: Alert severity (OK, WATCH, HIGH, CRITICAL).
        total_in_profession: Total workers in this profession.
        nationality_count: Workers of this nationality in profession.
        threshold_breached: Which threshold was breached.
        detected_date: When alert was first detected.
        resolved_date: When alert was resolved (if applicable).
    """
    
    __tablename__ = "dominance_alert"
    
    nationality_id = Column(
        Integer,
        ForeignKey("nationality.id"),
        nullable=False,
        index=True,
        doc="Foreign key to nationality"
    )
    profession_id = Column(
        Integer,
        ForeignKey("profession.id"),
        nullable=False,
        index=True,
        doc="Foreign key to profession"
    )
    share_pct = Column(
        Float,
        nullable=False,
        doc="Current nationality share in profession"
    )
    velocity = Column(
        Float,
        nullable=True,
        doc="Rate of share change (percentage points per 3 years)"
    )
    alert_level = Column(
        Enum(AlertLevel),
        nullable=False,
        index=True,
        doc="Alert severity level"
    )
    total_in_profession = Column(
        Integer,
        nullable=False,
        doc="Total workers in this profession"
    )
    nationality_count = Column(
        Integer,
        nullable=False,
        doc="Workers of this nationality in profession"
    )
    threshold_breached = Column(
        String(50),
        nullable=True,
        doc="Which threshold was breached"
    )
    detected_date = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="When alert was first detected"
    )
    resolved_date = Column(
        DateTime,
        nullable=True,
        doc="When alert was resolved"
    )
    
    # Relationships
    nationality = relationship("Nationality", back_populates="alerts")
    profession = relationship("Profession", back_populates="alerts")
    
    @property
    def is_active(self) -> bool:
        """
        Check if alert is still active.
        
        Returns:
            bool: True if not resolved.
        """
        return self.resolved_date is None
    
    @property
    def is_blocking(self) -> bool:
        """
        Check if alert should block new approvals.
        
        Returns:
            bool: True if CRITICAL level.
        """
        return self.alert_level == AlertLevel.CRITICAL
    
    @property
    def requires_partial(self) -> bool:
        """
        Check if alert requires partial approval only.
        
        Returns:
            bool: True if HIGH level.
        """
        return self.alert_level == AlertLevel.HIGH
    
    def __repr__(self) -> str:
        return f"<DominanceAlert(level={self.alert_level.value}, share={self.share_pct:.1%})>"
