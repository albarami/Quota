"""
Dashboard API routes.

Provides real-time monitoring data for nationalities.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas.models import (
    DashboardOverviewResponse,
    DashboardResponse,
    DominanceAlertSchema,
    TierStatusSchema,
    AlertLevelEnum,
    TierStatusEnum,
)
from src.engines import CapacityEngine, DominanceAlertEngine, QueueProcessor
from src.models import Nationality, NationalityTier, get_db

router = APIRouter()


def get_database():
    """Dependency to get database session."""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


@router.get("/{nationality_code}", response_model=DashboardResponse)
async def get_nationality_dashboard(
    nationality_code: str,
    db: Session = Depends(get_database)
):
    """
    Get live dashboard data for a specific nationality.
    
    Returns:
    - Cap, stock, headroom, utilization
    - Tier statuses (OPEN/RATIONED/LIMITED/CLOSED)
    - Active dominance alerts
    - Queue counts by tier
    - Projected outflow
    """
    # Get nationality
    nationality = db.query(Nationality).filter(
        Nationality.code == nationality_code.upper()
    ).first()
    
    if not nationality:
        raise HTTPException(status_code=404, detail=f"Nationality {nationality_code} not found")
    
    if not nationality.is_restricted:
        raise HTTPException(status_code=400, detail=f"Nationality {nationality_code} is not restricted")
    
    # Initialize engines
    capacity_engine = CapacityEngine(db)
    dominance_engine = DominanceAlertEngine(db)
    queue_processor = QueueProcessor(db)
    
    # Get capacity data
    try:
        headroom_result = capacity_engine.calculate_effective_headroom(nationality.id)
        tier_status_result = capacity_engine.calculate_tier_status(nationality.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Build tier status list
    tier_statuses = []
    tier_names = {1: "Primary", 2: "Secondary", 3: "Minor", 4: "Unusual"}
    
    # Get tier shares from database
    tiers = db.query(NationalityTier).filter(
        NationalityTier.nationality_id == nationality.id,
        NationalityTier.valid_to.is_(None)
    ).all()
    tier_shares = {t.tier_level: t.share_pct for t in tiers}
    
    for tier_level in [1, 2, 3, 4]:
        status = tier_status_result.tier_statuses.get(tier_level, "CLOSED")
        capacity = tier_status_result.tier_capacities.get(tier_level, 0)
        tier_statuses.append(TierStatusSchema(
            tier_level=tier_level,
            tier_name=tier_names[tier_level],
            status=TierStatusEnum(status.value if hasattr(status, 'value') else status),
            capacity=capacity,
            share_pct=tier_shares.get(tier_level),
        ))
    
    # Get dominance alerts
    alerts = dominance_engine.get_all_alerts_for_nationality(nationality.id)
    dominance_alerts = [
        DominanceAlertSchema(
            profession_id=a.profession_id,
            profession_name=a.profession_name,
            share_pct=a.share_pct,
            velocity=a.velocity,
            alert_level=AlertLevelEnum(a.alert_level.value),
            is_blocking=a.is_blocking,
        )
        for a in alerts
    ]
    
    # Get queue counts
    queue_status = queue_processor.get_queue_status(nationality.id)
    queue_counts = {tier: len(entries) for tier, entries in queue_status.items()}
    
    return DashboardResponse(
        nationality_id=nationality.id,
        nationality_code=nationality.code,
        nationality_name=nationality.name,
        cap=headroom_result.cap,
        stock=headroom_result.stock,
        headroom=headroom_result.effective_headroom,
        utilization_pct=headroom_result.utilization_pct,
        tier_statuses=tier_statuses,
        dominance_alerts=dominance_alerts,
        queue_counts=queue_counts,
        projected_outflow=headroom_result.projected_outflow,
        last_updated=datetime.utcnow(),
    )


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    db: Session = Depends(get_database)
):
    """
    Get overview of all restricted nationalities.
    
    Returns summary data for all restricted nationalities.
    """
    # Get all restricted nationalities
    nationalities = db.query(Nationality).filter(
        Nationality.is_restricted == True
    ).all()
    
    capacity_engine = CapacityEngine(db)
    dominance_engine = DominanceAlertEngine(db)
    queue_processor = QueueProcessor(db)
    
    nationality_data = []
    total_workers = 0
    total_headroom = 0
    
    for nationality in nationalities:
        try:
            headroom_result = capacity_engine.calculate_effective_headroom(nationality.id)
            tier_status_result = capacity_engine.calculate_tier_status(nationality.id)
            
            total_workers += headroom_result.stock
            total_headroom += headroom_result.effective_headroom
            
            # Build tier statuses
            tier_statuses = []
            tier_names = {1: "Primary", 2: "Secondary", 3: "Minor", 4: "Unusual"}
            for tier_level in [1, 2, 3, 4]:
                status = tier_status_result.tier_statuses.get(tier_level, "CLOSED")
                tier_statuses.append(TierStatusSchema(
                    tier_level=tier_level,
                    tier_name=tier_names[tier_level],
                    status=TierStatusEnum(status.value if hasattr(status, 'value') else status),
                    capacity=tier_status_result.tier_capacities.get(tier_level, 0),
                ))
            
            # Get alerts
            alerts = dominance_engine.get_all_alerts_for_nationality(nationality.id)
            dominance_alerts = [
                DominanceAlertSchema(
                    profession_id=a.profession_id,
                    profession_name=a.profession_name,
                    share_pct=a.share_pct,
                    velocity=a.velocity,
                    alert_level=AlertLevelEnum(a.alert_level.value),
                    is_blocking=a.is_blocking,
                )
                for a in alerts
            ]
            
            # Get queue counts
            queue_status = queue_processor.get_queue_status(nationality.id)
            queue_counts = {tier: len(entries) for tier, entries in queue_status.items()}
            
            nationality_data.append(DashboardResponse(
                nationality_id=nationality.id,
                nationality_code=nationality.code,
                nationality_name=nationality.name,
                cap=headroom_result.cap,
                stock=headroom_result.stock,
                headroom=headroom_result.effective_headroom,
                utilization_pct=headroom_result.utilization_pct,
                tier_statuses=tier_statuses,
                dominance_alerts=dominance_alerts,
                queue_counts=queue_counts,
                projected_outflow=headroom_result.projected_outflow,
                last_updated=datetime.utcnow(),
            ))
        except ValueError:
            # Skip nationalities without caps
            continue
    
    return DashboardOverviewResponse(
        nationalities=nationality_data,
        total_restricted=len(nationalities),
        total_workers=total_workers,
        total_headroom=total_headroom,
    )
