"""
Tier Discovery Engine.

Discovers demand patterns per nationality from historical request data.
Automatically classifies professions into Tiers 1-4 based on request share.

From Technical Specification Section 4:
- Tier 1 (Primary): >15% of requests
- Tier 2 (Secondary): 5-15% of requests
- Tier 3 (Minor): 1-5% of requests
- Tier 4 (Unusual): <1% of requests
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from config.settings import ParameterRegistry
from src.models import (
    Nationality,
    NationalityTier,
    Profession,
    QuotaRequest,
    RequestStatus,
)


@dataclass
class TierInfo:
    """Information about a tier classification."""
    
    nationality_id: int
    profession_id: int
    tier_level: int
    tier_name: str
    share_pct: float
    request_count: int
    is_current: bool


@dataclass
class TierDiscoveryResult:
    """Result of tier discovery for a nationality."""
    
    nationality_id: int
    nationality_code: str
    total_requests: int
    tiers: list[TierInfo]
    calculated_date: datetime


class TierDiscoveryEngine:
    """
    Discovers demand patterns per nationality from historical data.
    
    The engine analyzes historical request patterns to classify professions
    into tiers. This is a data-driven approach - the system discovers which
    professions are in demand rather than prescribing them.
    
    Attributes:
        db: SQLAlchemy database session.
        tier_1_threshold: Threshold for Tier 1 (default 0.15).
        tier_2_threshold: Threshold for Tier 2 (default 0.05).
        tier_3_threshold: Threshold for Tier 3 (default 0.01).
        hysteresis: Band to prevent tier oscillation (default 0.02).
        min_requests: Minimum sample size for tier assignment.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the Tier Discovery Engine.
        
        Args:
            db: SQLAlchemy database session.
        """
        self.db = db
        self.tier_1_threshold = ParameterRegistry.TIER_1_THRESHOLD
        self.tier_2_threshold = ParameterRegistry.TIER_2_THRESHOLD
        self.tier_3_threshold = ParameterRegistry.TIER_3_THRESHOLD
        self.hysteresis = ParameterRegistry.TIER_HYSTERESIS
        self.min_requests = ParameterRegistry.MIN_REQUESTS_FOR_TIER
    
    def discover_tiers(
        self,
        nationality_id: int,
        lookback_months: int = 12
    ) -> TierDiscoveryResult:
        """
        Discover tier classifications for a nationality based on historical requests.
        
        Analyzes the distribution of requests across professions and assigns
        tier levels based on the share of requests.
        
        Args:
            nationality_id: ID of the nationality to analyze.
            lookback_months: Number of months of historical data to consider.
            
        Returns:
            TierDiscoveryResult: Discovered tiers for the nationality.
        """
        # Get nationality info
        nationality = self.db.query(Nationality).filter(
            Nationality.id == nationality_id
        ).first()
        
        if not nationality:
            raise ValueError(f"Nationality {nationality_id} not found")
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_months * 30)
        
        # Get request counts by profession
        request_counts = self.db.query(
            QuotaRequest.profession_id,
            func.sum(QuotaRequest.requested_count).label("total_requested")
        ).filter(
            QuotaRequest.nationality_id == nationality_id,
            QuotaRequest.submitted_date >= start_date,
            QuotaRequest.status.in_([
                RequestStatus.APPROVED,
                RequestStatus.PARTIAL,
                RequestStatus.QUEUED,
                RequestStatus.BLOCKED,
            ])
        ).group_by(
            QuotaRequest.profession_id
        ).all()
        
        # Calculate total requests
        total_requests = sum(rc.total_requested or 0 for rc in request_counts)
        
        if total_requests < self.min_requests:
            # Not enough data for tier discovery
            return TierDiscoveryResult(
                nationality_id=nationality_id,
                nationality_code=nationality.code,
                total_requests=total_requests,
                tiers=[],
                calculated_date=datetime.utcnow(),
            )
        
        # Calculate shares and assign tiers
        tiers = []
        for rc in request_counts:
            share = (rc.total_requested or 0) / total_requests
            tier_level = self._calculate_tier_level(share, nationality_id, rc.profession_id)
            
            # Get profession name
            profession = self.db.query(Profession).filter(
                Profession.id == rc.profession_id
            ).first()
            
            tier_info = TierInfo(
                nationality_id=nationality_id,
                profession_id=rc.profession_id,
                tier_level=tier_level,
                tier_name=self._tier_name(tier_level),
                share_pct=share,
                request_count=rc.total_requested or 0,
                is_current=True,
            )
            tiers.append(tier_info)
        
        # Sort by share descending
        tiers.sort(key=lambda t: t.share_pct, reverse=True)
        
        return TierDiscoveryResult(
            nationality_id=nationality_id,
            nationality_code=nationality.code,
            total_requests=total_requests,
            tiers=tiers,
            calculated_date=datetime.utcnow(),
        )
    
    def _calculate_tier_level(
        self,
        share: float,
        nationality_id: int,
        profession_id: int
    ) -> int:
        """
        Calculate tier level with hysteresis to prevent oscillation.
        
        Args:
            share: Share of requests as decimal (0.0 to 1.0).
            nationality_id: Nationality ID for checking previous tier.
            profession_id: Profession ID for checking previous tier.
            
        Returns:
            int: Tier level (1-4).
        """
        # Get previous tier if exists
        previous_tier = self.db.query(NationalityTier).filter(
            NationalityTier.nationality_id == nationality_id,
            NationalityTier.profession_id == profession_id,
            NationalityTier.valid_to.is_(None)
        ).first()
        
        # Calculate base tier from thresholds
        if share >= self.tier_1_threshold:
            base_tier = 1
        elif share >= self.tier_2_threshold:
            base_tier = 2
        elif share >= self.tier_3_threshold:
            base_tier = 3
        else:
            base_tier = 4
        
        # Apply hysteresis if previous tier exists
        if previous_tier:
            prev_level = previous_tier.tier_level
            
            # If moving up (lower tier number = higher priority)
            if base_tier < prev_level:
                # Require exceeding threshold + hysteresis to move up
                if prev_level == 2 and share < self.tier_1_threshold + self.hysteresis:
                    return 2
                elif prev_level == 3 and share < self.tier_2_threshold + self.hysteresis:
                    return 3
                elif prev_level == 4 and share < self.tier_3_threshold + self.hysteresis:
                    return 4
            
            # If moving down (higher tier number = lower priority)
            elif base_tier > prev_level:
                # Require falling below threshold - hysteresis to move down
                if prev_level == 1 and share > self.tier_1_threshold - self.hysteresis:
                    return 1
                elif prev_level == 2 and share > self.tier_2_threshold - self.hysteresis:
                    return 2
                elif prev_level == 3 and share > self.tier_3_threshold - self.hysteresis:
                    return 3
        
        return base_tier
    
    def _tier_name(self, tier_level: int) -> str:
        """Get human-readable tier name."""
        names = {1: "Primary", 2: "Secondary", 3: "Minor", 4: "Unusual"}
        return names.get(tier_level, "Unknown")
    
    def get_tier_for_request(
        self,
        nationality_id: int,
        profession_id: int
    ) -> Optional[TierInfo]:
        """
        Get current tier classification for a nationality-profession pair.
        
        Args:
            nationality_id: Nationality ID.
            profession_id: Profession ID.
            
        Returns:
            TierInfo if tier exists, None otherwise.
        """
        tier = self.db.query(NationalityTier).filter(
            NationalityTier.nationality_id == nationality_id,
            NationalityTier.profession_id == profession_id,
            NationalityTier.valid_to.is_(None)
        ).first()
        
        if not tier:
            return None
        
        return TierInfo(
            nationality_id=tier.nationality_id,
            profession_id=tier.profession_id,
            tier_level=tier.tier_level,
            tier_name=self._tier_name(tier.tier_level),
            share_pct=tier.share_pct,
            request_count=tier.request_count or 0,
            is_current=tier.is_current,
        )
    
    def save_tiers(self, result: TierDiscoveryResult) -> None:
        """
        Save discovered tiers to the database.
        
        Invalidates previous tier assignments and creates new ones.
        
        Args:
            result: TierDiscoveryResult from discover_tiers().
        """
        today = date.today()
        
        # Invalidate existing tiers for this nationality
        self.db.query(NationalityTier).filter(
            NationalityTier.nationality_id == result.nationality_id,
            NationalityTier.valid_to.is_(None)
        ).update({NationalityTier.valid_to: today})
        
        # Create new tier records
        for tier_info in result.tiers:
            new_tier = NationalityTier(
                nationality_id=tier_info.nationality_id,
                profession_id=tier_info.profession_id,
                tier_level=tier_info.tier_level,
                share_pct=tier_info.share_pct,
                request_count=tier_info.request_count,
                calculated_date=result.calculated_date,
                valid_from=today,
            )
            self.db.add(new_tier)
        
        self.db.commit()
    
    def get_all_tiers_for_nationality(
        self,
        nationality_id: int
    ) -> list[TierInfo]:
        """
        Get all current tier classifications for a nationality.
        
        Args:
            nationality_id: Nationality ID.
            
        Returns:
            List of TierInfo sorted by tier level then share.
        """
        tiers = self.db.query(NationalityTier).filter(
            NationalityTier.nationality_id == nationality_id,
            NationalityTier.valid_to.is_(None)
        ).order_by(
            NationalityTier.tier_level,
            NationalityTier.share_pct.desc()
        ).all()
        
        return [
            TierInfo(
                nationality_id=t.nationality_id,
                profession_id=t.profession_id,
                tier_level=t.tier_level,
                tier_name=self._tier_name(t.tier_level),
                share_pct=t.share_pct,
                request_count=t.request_count or 0,
                is_current=t.is_current,
            )
            for t in tiers
        ]
