"""
Worker tracking models.

This module defines worker state tracking:
- WorkerState: Enum for worker states (IN_COUNTRY, COMMITTED, PENDING, QUEUED)
- WorkerStock: Individual worker records with state tracking

The worker state model is critical for accurate headroom calculation.
"""

import enum
from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class WorkerState(enum.Enum):
    """
    Worker state enumeration.
    
    From technical specification Section 10.1:
    - IN_COUNTRY: Active visa, physically present in Qatar
    - COMMITTED: Approved, visa issued, not yet arrived
    - PENDING: Application submitted, under review
    - QUEUED: Waiting for tier to open
    
    Headroom calculation uses these states differently:
    - IN_COUNTRY: Counted as stock
    - COMMITTED: Subtracted from headroom (arriving soon)
    - PENDING: Weighted at 80% approval rate
    - QUEUED: Not counted (waiting for capacity)
    """
    
    IN_COUNTRY = "IN_COUNTRY"  # Active visa, physically present
    COMMITTED = "COMMITTED"    # Approved, visa issued, not yet arrived
    PENDING = "PENDING"        # Application submitted, under review
    QUEUED = "QUEUED"          # Waiting for tier to open


class WorkerStock(BaseModel):
    """
    Individual worker record with state tracking.
    
    Represents a worker in the quota system. Maps to LMIS
    VRSP_VISA_DTL_ACTIVE and EMPLOYMENT tables.
    
    Attributes:
        worker_id: External worker identifier.
        nationality_id: Foreign key to nationality.
        profession_id: Foreign key to profession.
        establishment_id: Foreign key to establishment.
        state: Current worker state.
        visa_number: Visa reference number.
        visa_issue_date: When visa was issued.
        visa_expiry_date: When visa expires.
        employment_start: Employment start date.
        employment_end: Expected employment end date.
        entry_date: Date of entry to Qatar.
        exit_date: Date of exit from Qatar (if departed).
        is_final_exit: Whether exit is permanent.
    """
    
    __tablename__ = "worker_stock"
    
    worker_id = Column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
        doc="External worker identifier"
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
    establishment_id = Column(
        Integer,
        ForeignKey("establishment.id"),
        nullable=False,
        index=True,
        doc="Foreign key to establishment"
    )
    state = Column(
        Enum(WorkerState),
        default=WorkerState.IN_COUNTRY,
        nullable=False,
        index=True,
        doc="Current worker state"
    )
    visa_number = Column(
        String(50),
        nullable=True,
        doc="Visa reference number"
    )
    visa_issue_date = Column(
        Date,
        nullable=True,
        doc="When visa was issued"
    )
    visa_expiry_date = Column(
        Date,
        nullable=True,
        index=True,
        doc="When visa expires"
    )
    employment_start = Column(
        Date,
        nullable=True,
        doc="Employment start date"
    )
    employment_end = Column(
        Date,
        nullable=True,
        index=True,
        doc="Expected employment end date"
    )
    entry_date = Column(
        Date,
        nullable=True,
        doc="Date of entry to Qatar"
    )
    exit_date = Column(
        Date,
        nullable=True,
        doc="Date of exit from Qatar"
    )
    is_final_exit = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Whether exit is permanent (1=yes, 0=no)"
    )
    
    # Relationships
    nationality = relationship("Nationality", back_populates="workers")
    profession = relationship("Profession", back_populates="workers")
    establishment = relationship("Establishment", back_populates="workers")
    
    @property
    def is_in_country(self) -> bool:
        """Check if worker is currently in Qatar."""
        return self.state == WorkerState.IN_COUNTRY
    
    @property
    def is_committed(self) -> bool:
        """Check if worker is approved but not yet arrived."""
        return self.state == WorkerState.COMMITTED
    
    @property
    def is_pending(self) -> bool:
        """Check if worker application is pending."""
        return self.state == WorkerState.PENDING
    
    @property
    def days_until_visa_expiry(self) -> int | None:
        """
        Calculate days until visa expires.
        
        Returns:
            int: Days until expiry, or None if no expiry date.
        """
        if self.visa_expiry_date is None:
            return None
        delta = self.visa_expiry_date - date.today()
        return delta.days
    
    @property
    def days_until_employment_end(self) -> int | None:
        """
        Calculate days until employment ends.
        
        Returns:
            int: Days until end, or None if no end date.
        """
        if self.employment_end is None:
            return None
        delta = self.employment_end - date.today()
        return delta.days
    
    @property
    def is_expiring_soon(self) -> bool:
        """
        Check if visa expires within 30 days.
        
        Used for outflow projection.
        
        Returns:
            bool: True if expiring within 30 days.
        """
        days = self.days_until_visa_expiry
        return days is not None and 0 <= days <= 30
    
    @property
    def is_employment_ending_soon(self) -> bool:
        """
        Check if employment ends within 30 days.
        
        Used for outflow projection.
        
        Returns:
            bool: True if ending within 30 days.
        """
        days = self.days_until_employment_end
        return days is not None and 0 <= days <= 30
    
    def __repr__(self) -> str:
        return f"<WorkerStock(worker_id='{self.worker_id}', state={self.state.value})>"
