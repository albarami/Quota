"""
Core entity models for the quota system.

This module defines the fundamental entities:
- Nationality: Country/nationality classification
- Profession: Job/occupation definitions
- EconomicActivity: Industry/sector classification
- Establishment: Employer/company records

These models map to LMIS entities as defined in the technical specification.
"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class Nationality(BaseModel):
    """
    Nationality entity representing a country/nationality.
    
    Maps to LMIS NATIONALITY table. Used for tracking restricted
    nationalities and their quota allocations.
    
    Attributes:
        code: ISO 3-letter country code (e.g., 'EGY', 'IND').
        name: Full nationality name.
        name_ar: Arabic name (optional).
        is_restricted: Whether this nationality has quota restrictions.
        is_gcc: Whether this is a GCC country (exempt from restrictions).
        continent: Continent name for regional grouping.
    """
    
    __tablename__ = "nationality"
    
    code = Column(
        String(3),
        unique=True,
        nullable=False,
        index=True,
        doc="ISO 3-letter country code"
    )
    name = Column(
        String(100),
        nullable=False,
        doc="Full nationality name in English"
    )
    name_ar = Column(
        String(100),
        nullable=True,
        doc="Full nationality name in Arabic"
    )
    is_restricted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether this nationality has quota restrictions"
    )
    is_gcc = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this is a GCC country"
    )
    continent = Column(
        String(50),
        nullable=True,
        doc="Continent name for regional grouping"
    )
    
    # Relationships
    caps = relationship("NationalityCap", back_populates="nationality")
    tiers = relationship("NationalityTier", back_populates="nationality")
    alerts = relationship("DominanceAlert", back_populates="nationality")
    workers = relationship("WorkerStock", back_populates="nationality")
    requests = relationship("QuotaRequest", back_populates="nationality")
    
    def __repr__(self) -> str:
        return f"<Nationality(code='{self.code}', name='{self.name}')>"


class Profession(BaseModel):
    """
    Profession entity representing a job/occupation.
    
    Maps to LMIS PROFESSION table. Used for tier classification
    and demand pattern analysis.
    
    Attributes:
        code: Unique profession code.
        name: Profession name in English.
        name_ar: Profession name in Arabic (optional).
        category: Broad category (e.g., 'Construction', 'Healthcare').
        high_demand_flag: Whether this is a high-demand skill.
        non_skilled_fast_track: Eligible for fast-track processing.
        description: Detailed description of the profession.
    """
    
    __tablename__ = "profession"
    
    code = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique profession code"
    )
    name = Column(
        String(200),
        nullable=False,
        doc="Profession name in English"
    )
    name_ar = Column(
        String(200),
        nullable=True,
        doc="Profession name in Arabic"
    )
    category = Column(
        String(100),
        nullable=True,
        index=True,
        doc="Broad category (Construction, Healthcare, etc.)"
    )
    high_demand_flag = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether this is a high-demand skill (+50 priority points)"
    )
    non_skilled_fast_track = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Eligible for fast-track processing"
    )
    description = Column(
        Text,
        nullable=True,
        doc="Detailed description of the profession"
    )
    
    # Relationships
    tiers = relationship("NationalityTier", back_populates="profession")
    alerts = relationship("DominanceAlert", back_populates="profession")
    workers = relationship("WorkerStock", back_populates="profession")
    requests = relationship("QuotaRequest", back_populates="profession")
    
    def __repr__(self) -> str:
        return f"<Profession(code='{self.code}', name='{self.name}')>"


class EconomicActivity(BaseModel):
    """
    Economic activity/sector entity.
    
    Maps to LMIS ECONOMIC_ACTIVITY table. Used for sector
    classification and strategic sector weighting.
    
    Attributes:
        code: Unique activity code.
        name: Activity name in English.
        name_ar: Activity name in Arabic (optional).
        sector_group: High-level sector grouping.
        is_strategic: Whether this is a strategic sector (+30 priority).
        strategic_weight: Weight multiplier for strategic sectors.
    """
    
    __tablename__ = "economic_activity"
    
    code = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique activity code"
    )
    name = Column(
        String(200),
        nullable=False,
        doc="Activity name in English"
    )
    name_ar = Column(
        String(200),
        nullable=True,
        doc="Activity name in Arabic"
    )
    sector_group = Column(
        String(100),
        nullable=True,
        index=True,
        doc="High-level sector grouping"
    )
    is_strategic = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether this is a strategic sector"
    )
    strategic_weight = Column(
        Float,
        default=1.0,
        nullable=False,
        doc="Weight multiplier for strategic sectors"
    )
    
    # Relationships
    establishments = relationship("Establishment", back_populates="activity")
    
    def __repr__(self) -> str:
        return f"<EconomicActivity(code='{self.code}', name='{self.name}')>"


class Establishment(BaseModel):
    """
    Establishment/employer entity.
    
    Represents a company or employer in Qatar. Tracks labor
    approval utilization for priority scoring.
    
    Attributes:
        name: Establishment name.
        license_number: Business license number.
        activity_id: Foreign key to economic activity.
        total_approved: Total approved labor quota.
        total_used: Currently used labor quota.
        size_category: Size classification (Small, Medium, Large).
        is_active: Whether the establishment is currently active.
    """
    
    __tablename__ = "establishment"
    
    name = Column(
        String(300),
        nullable=False,
        doc="Establishment name"
    )
    license_number = Column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
        doc="Business license number"
    )
    activity_id = Column(
        Integer,
        ForeignKey("economic_activity.id"),
        nullable=True,
        index=True,
        doc="Foreign key to economic activity"
    )
    total_approved = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Total approved labor quota"
    )
    total_used = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Currently used labor quota"
    )
    size_category = Column(
        String(20),
        nullable=True,
        doc="Size classification (Small, Medium, Large)"
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the establishment is currently active"
    )
    
    # Relationships
    activity = relationship("EconomicActivity", back_populates="establishments")
    workers = relationship("WorkerStock", back_populates="establishment")
    requests = relationship("QuotaRequest", back_populates="establishment")
    
    @property
    def utilization_rate(self) -> float:
        """
        Calculate labor utilization rate.
        
        Returns:
            float: Utilization rate (0.0 to 1.0), or 0 if no approved quota.
        """
        if self.total_approved == 0:
            return 0.0
        return self.total_used / self.total_approved
    
    @property
    def is_small(self) -> bool:
        """
        Check if establishment is small (<50 workers).
        
        Returns:
            bool: True if small establishment.
        """
        return self.total_approved < 50
    
    def __repr__(self) -> str:
        return f"<Establishment(name='{self.name}', utilization={self.utilization_rate:.1%})>"
