"""
Capacity Engine.

Real-time calculation of headroom and tier availability.
Implements the core capacity formula from Technical Specification Section 10.2.

Core Formula:
    effective_headroom = cap - stock - committed - (pending * 0.8) + (outflow * 0.75)
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from config.settings import ParameterRegistry
from src.models import (
    Nationality,
    NationalityCap,
    NationalityTier,
    QuotaRequest,
    RequestStatus,
    WorkerState,
    WorkerStock,
)


class TierStatus(Enum):
    """Tier availability status."""
    
    OPEN = "OPEN"          # Full capacity available
    RATIONED = "RATIONED"  # Limited capacity, priority applies
    LIMITED = "LIMITED"    # Very limited capacity
    CLOSED = "CLOSED"      # No capacity available


@dataclass
class HeadroomResult:
    """Result of headroom calculation."""
    
    nationality_id: int
    cap: int
    stock: int
    committed: int
    pending: int
    projected_outflow: int
    raw_headroom: int
    effective_headroom: int
    utilization_pct: float
    calculated_at: datetime


@dataclass
class TierStatusResult:
    """Status of all tiers for a nationality."""
    
    nationality_id: int
    headroom: int
    tier_statuses: dict[int, TierStatus]  # tier_level -> status
    tier_capacities: dict[int, int]       # tier_level -> available slots
    calculated_at: datetime


@dataclass
class OutflowProjection:
    """Projected workforce outflow."""
    
    nationality_id: int
    projection_days: int
    final_exit_visas: int
    expiring_contracts: int
    non_renewal_ratio: float
    raw_projection: int
    adjusted_projection: int  # After confidence factor
    calculated_at: datetime


class CapacityEngine:
    """
    Real-time calculation of headroom and tier availability.
    
    The engine continuously recalculates capacity based on:
    - Current worker stock (IN_COUNTRY state)
    - Pipeline commitments (COMMITTED + PENDING states)
    - Projected outflow (final exits only)
    
    Tier statuses are determined by comparing headroom to tier demand.
    Higher tiers (Tier 1) are protected first.
    
    Attributes:
        db: SQLAlchemy database session.
        confidence_factor: Conservative buffer on outflow projections.
        pending_approval_rate: Expected approval rate for pending requests.
        projection_horizon: Days to look ahead for outflow projection.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the Capacity Engine.
        
        Args:
            db: SQLAlchemy database session.
        """
        self.db = db
        self.confidence_factor = ParameterRegistry.OUTFLOW_CONFIDENCE_FACTOR
        self.pending_approval_rate = ParameterRegistry.PENDING_APPROVAL_RATE
        self.projection_horizon = ParameterRegistry.PROJECTION_HORIZON_DAYS
    
    def calculate_effective_headroom(
        self,
        nationality_id: int,
        include_outflow: bool = True
    ) -> HeadroomResult:
        """
        Calculate effective headroom for a nationality.
        
        Formula from spec Section 10.2:
        effective_headroom = cap - stock - committed - (pending * 0.8) + (outflow * 0.75)
        
        Args:
            nationality_id: ID of the nationality.
            include_outflow: Whether to include projected outflow.
            
        Returns:
            HeadroomResult: Detailed headroom calculation.
        """
        # Get current cap
        current_year = date.today().year
        cap_record = self.db.query(NationalityCap).filter(
            NationalityCap.nationality_id == nationality_id,
            NationalityCap.year == current_year
        ).first()
        
        if not cap_record:
            raise ValueError(f"No cap set for nationality {nationality_id} in {current_year}")
        
        cap = cap_record.cap_limit
        
        # Count workers by state
        stock = self._count_workers_by_state(nationality_id, WorkerState.IN_COUNTRY)
        committed = self._count_workers_by_state(nationality_id, WorkerState.COMMITTED)
        pending = self._count_pending_requests(nationality_id)
        
        # Project outflow if requested
        if include_outflow:
            outflow_result = self.project_outflow(nationality_id)
            projected_outflow = outflow_result.adjusted_projection
        else:
            projected_outflow = 0
        
        # Calculate headroom
        raw_headroom = cap - stock - committed
        pending_weighted = int(pending * self.pending_approval_rate)
        effective_headroom = raw_headroom - pending_weighted + projected_outflow
        
        # Ensure non-negative
        effective_headroom = max(0, effective_headroom)
        
        # Calculate utilization
        utilization = stock / cap if cap > 0 else 0.0
        
        return HeadroomResult(
            nationality_id=nationality_id,
            cap=cap,
            stock=stock,
            committed=committed,
            pending=pending,
            projected_outflow=projected_outflow,
            raw_headroom=raw_headroom,
            effective_headroom=effective_headroom,
            utilization_pct=utilization,
            calculated_at=datetime.utcnow(),
        )
    
    def _count_workers_by_state(
        self,
        nationality_id: int,
        state: WorkerState
    ) -> int:
        """Count workers in a specific state."""
        count = self.db.query(func.count(WorkerStock.id)).filter(
            WorkerStock.nationality_id == nationality_id,
            WorkerStock.state == state
        ).scalar()
        return count or 0
    
    def _count_pending_requests(self, nationality_id: int) -> int:
        """Count workers in pending requests."""
        result = self.db.query(
            func.sum(QuotaRequest.requested_count)
        ).filter(
            QuotaRequest.nationality_id == nationality_id,
            QuotaRequest.status.in_([
                RequestStatus.SUBMITTED,
                RequestStatus.PROCESSING
            ])
        ).scalar()
        return result or 0
    
    def calculate_tier_status(
        self,
        nationality_id: int
    ) -> TierStatusResult:
        """
        Calculate tier availability status for a nationality.
        
        Tiers are protected in order: Tier 1 first, then Tier 2, etc.
        A tier only opens when headroom exceeds the demand of higher tiers.
        
        Status logic from spec Section 5.1:
        - OPEN: headroom >= tier_demand
        - RATIONED: 0 < headroom < tier_demand (for Tier 1)
        - LIMITED: 0 < surplus < tier_demand (for Tier 2+)
        - CLOSED: no surplus available
        
        Args:
            nationality_id: ID of the nationality.
            
        Returns:
            TierStatusResult: Status of all tiers.
        """
        headroom_result = self.calculate_effective_headroom(nationality_id)
        headroom = headroom_result.effective_headroom
        
        # Get tier demand projections
        tier_demands = self._calculate_tier_demands(nationality_id)
        
        tier_statuses: dict[int, TierStatus] = {}
        tier_capacities: dict[int, int] = {}
        
        remaining_headroom = headroom
        
        for tier_level in [1, 2, 3, 4]:
            tier_demand = tier_demands.get(tier_level, 0)
            
            if tier_level == 1:
                # Tier 1 logic
                if remaining_headroom >= tier_demand:
                    tier_statuses[1] = TierStatus.OPEN
                    tier_capacities[1] = tier_demand
                    remaining_headroom -= tier_demand
                elif remaining_headroom > 0:
                    tier_statuses[1] = TierStatus.RATIONED
                    tier_capacities[1] = remaining_headroom
                    remaining_headroom = 0
                else:
                    tier_statuses[1] = TierStatus.CLOSED
                    tier_capacities[1] = 0
            else:
                # Tier 2+ logic - only opens when higher tiers are satisfied
                if remaining_headroom >= tier_demand:
                    tier_statuses[tier_level] = TierStatus.OPEN
                    tier_capacities[tier_level] = tier_demand
                    remaining_headroom -= tier_demand
                elif remaining_headroom > 0:
                    tier_statuses[tier_level] = TierStatus.LIMITED
                    tier_capacities[tier_level] = remaining_headroom
                    remaining_headroom = 0
                else:
                    tier_statuses[tier_level] = TierStatus.CLOSED
                    tier_capacities[tier_level] = 0
        
        return TierStatusResult(
            nationality_id=nationality_id,
            headroom=headroom,
            tier_statuses=tier_statuses,
            tier_capacities=tier_capacities,
            calculated_at=datetime.utcnow(),
        )
    
    def _calculate_tier_demands(self, nationality_id: int) -> dict[int, int]:
        """
        Calculate projected demand for each tier.
        
        Uses historical average monthly inflow by tier.
        """
        # Get tier shares
        tiers = self.db.query(NationalityTier).filter(
            NationalityTier.nationality_id == nationality_id,
            NationalityTier.valid_to.is_(None)
        ).all()
        
        # Calculate total monthly inflow (average from last 12 months)
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        monthly_inflow = self.db.query(
            func.sum(QuotaRequest.approved_count)
        ).filter(
            QuotaRequest.nationality_id == nationality_id,
            QuotaRequest.submitted_date >= twelve_months_ago,
            QuotaRequest.status.in_([RequestStatus.APPROVED, RequestStatus.PARTIAL])
        ).scalar() or 0
        
        avg_monthly_inflow = monthly_inflow / 12
        
        # Calculate demand per tier
        tier_demands = {1: 0, 2: 0, 3: 0, 4: 0}
        
        for tier in tiers:
            demand = int(avg_monthly_inflow * tier.share_pct)
            tier_demands[tier.tier_level] = tier_demands.get(tier.tier_level, 0) + demand
        
        return tier_demands
    
    def project_outflow(
        self,
        nationality_id: int,
        days: Optional[int] = None
    ) -> OutflowProjection:
        """
        Project workforce outflow for a nationality.
        
        From spec Section 5.3:
        Outflow = FINAL EXITS ONLY (end of employment)
        NOT vacation travel, Ramadan visits, business trips
        
        Components:
        - FINAL_EXIT_VISAS scheduled
        - EXPIRING_CONTRACTS × NON_RENEWAL_RATIO
        
        Args:
            nationality_id: ID of the nationality.
            days: Projection horizon in days (default from settings).
            
        Returns:
            OutflowProjection: Projected outflow details.
        """
        if days is None:
            days = self.projection_horizon
        
        end_date = date.today() + timedelta(days=days)
        
        # Count final exit visas (workers marked for final exit)
        final_exit_visas = self.db.query(func.count(WorkerStock.id)).filter(
            WorkerStock.nationality_id == nationality_id,
            WorkerStock.state == WorkerState.IN_COUNTRY,
            WorkerStock.is_final_exit == 1,
            WorkerStock.visa_expiry_date <= end_date
        ).scalar() or 0
        
        # Count expiring contracts
        expiring_contracts = self.db.query(func.count(WorkerStock.id)).filter(
            WorkerStock.nationality_id == nationality_id,
            WorkerStock.state == WorkerState.IN_COUNTRY,
            WorkerStock.employment_end <= end_date,
            WorkerStock.employment_end >= date.today()
        ).scalar() or 0
        
        # Calculate non-renewal ratio from historical data
        # (Typical range: 0.15-0.35 - most contracts renew)
        non_renewal_ratio = self._calculate_non_renewal_ratio(nationality_id)
        
        # Calculate projections
        raw_projection = final_exit_visas + int(expiring_contracts * non_renewal_ratio)
        adjusted_projection = int(raw_projection * self.confidence_factor)
        
        return OutflowProjection(
            nationality_id=nationality_id,
            projection_days=days,
            final_exit_visas=final_exit_visas,
            expiring_contracts=expiring_contracts,
            non_renewal_ratio=non_renewal_ratio,
            raw_projection=raw_projection,
            adjusted_projection=adjusted_projection,
            calculated_at=datetime.utcnow(),
        )
    
    def _calculate_non_renewal_ratio(self, nationality_id: int) -> float:
        """
        Calculate historical non-renewal ratio.
        
        Returns average ratio of contracts that don't renew.
        Default to 0.25 if no historical data.
        """
        # In a real system, this would analyze historical departures
        # vs contract expirations. For now, use a reasonable default.
        return 0.25
    
    def get_capacity_snapshot(
        self,
        nationality_id: int
    ) -> dict:
        """
        Get a complete capacity snapshot for audit logging.
        
        Returns all capacity-related values as a dictionary.
        """
        headroom = self.calculate_effective_headroom(nationality_id)
        tier_status = self.calculate_tier_status(nationality_id)
        
        return {
            "nationality_id": nationality_id,
            "cap": headroom.cap,
            "stock": headroom.stock,
            "committed": headroom.committed,
            "pending": headroom.pending,
            "projected_outflow": headroom.projected_outflow,
            "raw_headroom": headroom.raw_headroom,
            "effective_headroom": headroom.effective_headroom,
            "utilization_pct": headroom.utilization_pct,
            "tier_statuses": {
                k: v.value for k, v in tier_status.tier_statuses.items()
            },
            "tier_capacities": tier_status.tier_capacities,
            "calculated_at": datetime.utcnow().isoformat(),
        }
