"""
Dominance Alert Engine.

Monitors nationality concentration within professions to prevent over-reliance.
This is an additional check beyond tier allocation.

From Technical Specification Section 7:
- CRITICAL: >50% share + >10pp velocity -> Block new approvals
- HIGH: 40-50% share + >5pp velocity -> Partial approve only
- WATCH: 30-40% share -> Flag for review
- OK: <30% share -> Normal processing

MIN_PROFESSION_SIZE = 200 (dominance rules only apply above this)
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from config.settings import ParameterRegistry
from src.models import (
    AlertLevel,
    DominanceAlert,
    Nationality,
    Profession,
    WorkerState,
    WorkerStock,
)


@dataclass
class DominanceCheckResult:
    """Result of a dominance check."""
    
    nationality_id: int
    profession_id: int
    nationality_code: str
    profession_name: str
    share_pct: float
    velocity: float
    alert_level: AlertLevel
    total_in_profession: int
    nationality_count: int
    is_blocking: bool
    is_partial_only: bool
    requires_review: bool
    message: str


@dataclass
class VelocityResult:
    """Result of velocity calculation."""
    
    nationality_id: int
    profession_id: int
    current_share: float
    historical_share: float
    velocity_pct: float  # Percentage points change per period
    period_years: int
    trend: str  # "increasing", "stable", "decreasing"


class DominanceAlertEngine:
    """
    Monitors nationality concentration within professions.
    
    Even when a tier is open, the system checks for dominance risk.
    A nationality can be blocked from a profession if its share is
    too high, preventing over-concentration.
    
    Attributes:
        db: SQLAlchemy database session.
        critical_threshold: Share threshold for CRITICAL alert.
        high_threshold: Share threshold for HIGH alert.
        watch_threshold: Share threshold for WATCH alert.
        velocity_critical: Velocity threshold for CRITICAL.
        min_profession_size: Minimum profession size for rules to apply.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the Dominance Alert Engine.
        
        Args:
            db: SQLAlchemy database session.
        """
        self.db = db
        self.critical_threshold = ParameterRegistry.DOMINANCE_CRITICAL
        self.high_threshold = ParameterRegistry.DOMINANCE_HIGH
        self.watch_threshold = ParameterRegistry.DOMINANCE_WATCH
        self.velocity_critical = ParameterRegistry.VELOCITY_CRITICAL
        self.min_profession_size = ParameterRegistry.MIN_PROFESSION_SIZE
    
    def check_dominance(
        self,
        nationality_id: int,
        profession_id: int
    ) -> DominanceCheckResult:
        """
        Check dominance status for a nationality-profession pair.
        
        Args:
            nationality_id: ID of the nationality.
            profession_id: ID of the profession.
            
        Returns:
            DominanceCheckResult: Complete dominance analysis.
        """
        # Get nationality and profession info
        nationality = self.db.query(Nationality).filter(
            Nationality.id == nationality_id
        ).first()
        profession = self.db.query(Profession).filter(
            Profession.id == profession_id
        ).first()
        
        if not nationality or not profession:
            raise ValueError("Invalid nationality or profession ID")
        
        # Count workers in profession (all nationalities)
        total_in_profession = self.db.query(func.count(WorkerStock.id)).filter(
            WorkerStock.profession_id == profession_id,
            WorkerStock.state == WorkerState.IN_COUNTRY
        ).scalar() or 0
        
        # Count workers of this nationality in profession
        nationality_count = self.db.query(func.count(WorkerStock.id)).filter(
            WorkerStock.nationality_id == nationality_id,
            WorkerStock.profession_id == profession_id,
            WorkerStock.state == WorkerState.IN_COUNTRY
        ).scalar() or 0
        
        # Calculate share
        if total_in_profession == 0:
            share_pct = 0.0
        else:
            share_pct = nationality_count / total_in_profession
        
        # Calculate velocity
        velocity_result = self.calculate_velocity(nationality_id, profession_id)
        velocity = velocity_result.velocity_pct
        
        # Determine alert level
        alert_level = self._determine_alert_level(
            share_pct, velocity, total_in_profession
        )
        
        # Determine actions
        is_blocking = alert_level == AlertLevel.CRITICAL
        is_partial_only = alert_level == AlertLevel.HIGH
        requires_review = alert_level == AlertLevel.WATCH
        
        # Generate message
        message = self._generate_message(
            nationality.code, profession.name, share_pct,
            velocity, alert_level, total_in_profession
        )
        
        return DominanceCheckResult(
            nationality_id=nationality_id,
            profession_id=profession_id,
            nationality_code=nationality.code,
            profession_name=profession.name,
            share_pct=share_pct,
            velocity=velocity,
            alert_level=alert_level,
            total_in_profession=total_in_profession,
            nationality_count=nationality_count,
            is_blocking=is_blocking,
            is_partial_only=is_partial_only,
            requires_review=requires_review,
            message=message,
        )
    
    def _determine_alert_level(
        self,
        share: float,
        velocity: float,
        profession_size: int
    ) -> AlertLevel:
        """
        Determine alert level based on share, velocity, and size.
        
        Args:
            share: Nationality share in profession (0.0 to 1.0).
            velocity: Share change rate (percentage points per 3 years).
            profession_size: Total workers in profession.
            
        Returns:
            AlertLevel: Appropriate alert level.
        """
        # Dominance rules only apply above minimum profession size
        if profession_size < self.min_profession_size:
            return AlertLevel.OK
        
        # Check thresholds with velocity consideration
        if share >= self.critical_threshold:
            return AlertLevel.CRITICAL
        elif share >= self.high_threshold:
            # HIGH also triggered by accelerating growth
            if velocity >= self.velocity_critical:
                return AlertLevel.CRITICAL
            return AlertLevel.HIGH
        elif share >= self.watch_threshold:
            # WATCH with high velocity escalates to HIGH
            if velocity >= self.velocity_critical * 0.5:  # >5pp/3yr
                return AlertLevel.HIGH
            return AlertLevel.WATCH
        else:
            return AlertLevel.OK
    
    def _generate_message(
        self,
        nationality_code: str,
        profession_name: str,
        share: float,
        velocity: float,
        alert_level: AlertLevel,
        profession_size: int
    ) -> str:
        """Generate human-readable alert message."""
        if profession_size < self.min_profession_size:
            return f"Profession too small ({profession_size}) for dominance rules"
        
        messages = {
            AlertLevel.CRITICAL: (
                f"CRITICAL: {nationality_code} share in {profession_name} is "
                f"{share:.1%} (>{self.critical_threshold:.0%}). "
                f"Velocity: {velocity:+.1%}/3yr. NEW APPROVALS BLOCKED."
            ),
            AlertLevel.HIGH: (
                f"HIGH: {nationality_code} share in {profession_name} is "
                f"{share:.1%} ({self.high_threshold:.0%}-{self.critical_threshold:.0%}). "
                f"Velocity: {velocity:+.1%}/3yr. PARTIAL APPROVALS ONLY."
            ),
            AlertLevel.WATCH: (
                f"WATCH: {nationality_code} share in {profession_name} is "
                f"{share:.1%} ({self.watch_threshold:.0%}-{self.high_threshold:.0%}). "
                f"Velocity: {velocity:+.1%}/3yr. Flagged for review."
            ),
            AlertLevel.OK: (
                f"OK: {nationality_code} share in {profession_name} is "
                f"{share:.1%} (<{self.watch_threshold:.0%}). Normal processing."
            ),
        }
        return messages.get(alert_level, "Unknown alert level")
    
    def calculate_velocity(
        self,
        nationality_id: int,
        profession_id: int,
        years: int = 3
    ) -> VelocityResult:
        """
        Calculate share change velocity over time.
        
        Velocity = (current_share - historical_share) / years
        
        Args:
            nationality_id: ID of the nationality.
            profession_id: ID of the profession.
            years: Number of years to look back.
            
        Returns:
            VelocityResult: Velocity analysis.
        """
        # Calculate current share
        total_current = self.db.query(func.count(WorkerStock.id)).filter(
            WorkerStock.profession_id == profession_id,
            WorkerStock.state == WorkerState.IN_COUNTRY
        ).scalar() or 0
        
        nat_current = self.db.query(func.count(WorkerStock.id)).filter(
            WorkerStock.nationality_id == nationality_id,
            WorkerStock.profession_id == profession_id,
            WorkerStock.state == WorkerState.IN_COUNTRY
        ).scalar() or 0
        
        current_share = nat_current / total_current if total_current > 0 else 0.0
        
        # Calculate historical share (simplified - in production would use historical snapshots)
        # For now, estimate based on employment start dates
        historical_date = datetime.utcnow() - timedelta(days=years * 365)
        
        total_historical = self.db.query(func.count(WorkerStock.id)).filter(
            WorkerStock.profession_id == profession_id,
            WorkerStock.state == WorkerState.IN_COUNTRY,
            WorkerStock.employment_start <= historical_date.date()
        ).scalar() or 0
        
        nat_historical = self.db.query(func.count(WorkerStock.id)).filter(
            WorkerStock.nationality_id == nationality_id,
            WorkerStock.profession_id == profession_id,
            WorkerStock.state == WorkerState.IN_COUNTRY,
            WorkerStock.employment_start <= historical_date.date()
        ).scalar() or 0
        
        historical_share = nat_historical / total_historical if total_historical > 0 else current_share
        
        # Calculate velocity (percentage points change)
        velocity = current_share - historical_share
        
        # Determine trend
        if velocity > 0.02:
            trend = "increasing"
        elif velocity < -0.02:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return VelocityResult(
            nationality_id=nationality_id,
            profession_id=profession_id,
            current_share=current_share,
            historical_share=historical_share,
            velocity_pct=velocity,
            period_years=years,
            trend=trend,
        )
    
    def get_all_alerts_for_nationality(
        self,
        nationality_id: int
    ) -> list[DominanceCheckResult]:
        """
        Get all active dominance alerts for a nationality.
        
        Args:
            nationality_id: ID of the nationality.
            
        Returns:
            List of DominanceCheckResult for each alerted profession.
        """
        # Get professions where this nationality has workers
        professions = self.db.query(WorkerStock.profession_id).filter(
            WorkerStock.nationality_id == nationality_id,
            WorkerStock.state == WorkerState.IN_COUNTRY
        ).distinct().all()
        
        alerts = []
        for (profession_id,) in professions:
            result = self.check_dominance(nationality_id, profession_id)
            if result.alert_level != AlertLevel.OK:
                alerts.append(result)
        
        # Sort by alert level severity
        level_order = {
            AlertLevel.CRITICAL: 0,
            AlertLevel.HIGH: 1,
            AlertLevel.WATCH: 2,
            AlertLevel.OK: 3,
        }
        alerts.sort(key=lambda a: (level_order[a.alert_level], -a.share_pct))
        
        return alerts
    
    def save_alert(self, result: DominanceCheckResult) -> Optional[DominanceAlert]:
        """
        Save or update a dominance alert in the database.
        
        Args:
            result: DominanceCheckResult to save.
            
        Returns:
            DominanceAlert record if created/updated, None if OK status.
        """
        if result.alert_level == AlertLevel.OK:
            # Resolve any existing alerts
            self.db.query(DominanceAlert).filter(
                DominanceAlert.nationality_id == result.nationality_id,
                DominanceAlert.profession_id == result.profession_id,
                DominanceAlert.resolved_date.is_(None)
            ).update({DominanceAlert.resolved_date: datetime.utcnow()})
            self.db.commit()
            return None
        
        # Check for existing active alert
        existing = self.db.query(DominanceAlert).filter(
            DominanceAlert.nationality_id == result.nationality_id,
            DominanceAlert.profession_id == result.profession_id,
            DominanceAlert.resolved_date.is_(None)
        ).first()
        
        if existing:
            # Update existing alert
            existing.share_pct = result.share_pct
            existing.velocity = result.velocity
            existing.alert_level = result.alert_level
            existing.total_in_profession = result.total_in_profession
            existing.nationality_count = result.nationality_count
            self.db.commit()
            return existing
        else:
            # Create new alert
            alert = DominanceAlert(
                nationality_id=result.nationality_id,
                profession_id=result.profession_id,
                share_pct=result.share_pct,
                velocity=result.velocity,
                alert_level=result.alert_level,
                total_in_profession=result.total_in_profession,
                nationality_count=result.nationality_count,
                threshold_breached=f"{result.alert_level.value}_THRESHOLD",
                detected_date=datetime.utcnow(),
            )
            self.db.add(alert)
            self.db.commit()
            return alert
    
    def get_dominance_snapshot(
        self,
        nationality_id: int,
        profession_id: int
    ) -> dict:
        """
        Get a complete dominance snapshot for audit logging.
        
        Returns all dominance-related values as a dictionary.
        """
        result = self.check_dominance(nationality_id, profession_id)
        
        return {
            "nationality_id": result.nationality_id,
            "profession_id": result.profession_id,
            "share_pct": result.share_pct,
            "velocity": result.velocity,
            "alert_level": result.alert_level.value,
            "total_in_profession": result.total_in_profession,
            "nationality_count": result.nationality_count,
            "is_blocking": result.is_blocking,
            "calculated_at": datetime.utcnow().isoformat(),
        }
