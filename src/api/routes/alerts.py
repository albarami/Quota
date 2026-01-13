"""
Dominance Alerts API routes.

Provides endpoints for viewing and managing dominance alerts.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas.models import (
    AlertDetailSchema,
    AlertLevelEnum,
    AlertsResponse,
    CriticalAlertsResponse,
)
from src.engines import DominanceAlertEngine
from src.models import (
    DominanceAlert,
    Nationality,
    Profession,
    get_db,
)

router = APIRouter()


def get_database():
    """Dependency to get database session."""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


@router.get("/{nationality_code}", response_model=AlertsResponse)
async def get_alerts_for_nationality(
    nationality_code: str,
    db: Session = Depends(get_database)
):
    """
    Get all active dominance alerts for a nationality.
    """
    nationality = db.query(Nationality).filter(
        Nationality.code == nationality_code.upper()
    ).first()
    
    if not nationality:
        raise HTTPException(status_code=404, detail=f"Nationality {nationality_code} not found")
    
    # Get alerts from database
    alerts = db.query(DominanceAlert).filter(
        DominanceAlert.nationality_id == nationality.id,
        DominanceAlert.resolved_date.is_(None)
    ).all()
    
    alert_details = []
    for alert in alerts:
        profession = db.query(Profession).filter(
            Profession.id == alert.profession_id
        ).first()
        
        alert_details.append(AlertDetailSchema(
            id=alert.id,
            nationality_id=alert.nationality_id,
            nationality_code=nationality.code,
            profession_id=alert.profession_id,
            profession_name=profession.name if profession else "Unknown",
            share_pct=alert.share_pct,
            velocity=alert.velocity or 0,
            alert_level=AlertLevelEnum(alert.alert_level.value),
            total_in_profession=alert.total_in_profession,
            nationality_count=alert.nationality_count,
            detected_date=alert.detected_date,
            is_active=alert.is_active,
        ))
    
    return AlertsResponse(
        nationality_id=nationality.id,
        nationality_code=nationality.code,
        alerts=alert_details,
        total_count=len(alert_details),
    )


@router.get("/critical", response_model=CriticalAlertsResponse)
async def get_critical_alerts(
    db: Session = Depends(get_database)
):
    """
    Get all critical dominance alerts across all nationalities.
    
    Critical alerts block new approvals and require immediate attention.
    """
    from src.models.quota import AlertLevel
    
    # Get critical alerts
    alerts = db.query(DominanceAlert).filter(
        DominanceAlert.alert_level == AlertLevel.CRITICAL,
        DominanceAlert.resolved_date.is_(None)
    ).all()
    
    alert_details = []
    for alert in alerts:
        nationality = db.query(Nationality).filter(
            Nationality.id == alert.nationality_id
        ).first()
        profession = db.query(Profession).filter(
            Profession.id == alert.profession_id
        ).first()
        
        alert_details.append(AlertDetailSchema(
            id=alert.id,
            nationality_id=alert.nationality_id,
            nationality_code=nationality.code if nationality else "UNK",
            profession_id=alert.profession_id,
            profession_name=profession.name if profession else "Unknown",
            share_pct=alert.share_pct,
            velocity=alert.velocity or 0,
            alert_level=AlertLevelEnum.CRITICAL,
            total_in_profession=alert.total_in_profession,
            nationality_count=alert.nationality_count,
            detected_date=alert.detected_date,
            is_active=True,
        ))
    
    return CriticalAlertsResponse(
        alerts=alert_details,
        total_count=len(alert_details),
    )


@router.get("/high", response_model=CriticalAlertsResponse)
async def get_high_alerts(
    db: Session = Depends(get_database)
):
    """
    Get all HIGH level dominance alerts.
    
    HIGH alerts require partial approval only.
    """
    from src.models.quota import AlertLevel
    
    alerts = db.query(DominanceAlert).filter(
        DominanceAlert.alert_level == AlertLevel.HIGH,
        DominanceAlert.resolved_date.is_(None)
    ).all()
    
    alert_details = []
    for alert in alerts:
        nationality = db.query(Nationality).filter(
            Nationality.id == alert.nationality_id
        ).first()
        profession = db.query(Profession).filter(
            Profession.id == alert.profession_id
        ).first()
        
        alert_details.append(AlertDetailSchema(
            id=alert.id,
            nationality_id=alert.nationality_id,
            nationality_code=nationality.code if nationality else "UNK",
            profession_id=alert.profession_id,
            profession_name=profession.name if profession else "Unknown",
            share_pct=alert.share_pct,
            velocity=alert.velocity or 0,
            alert_level=AlertLevelEnum.HIGH,
            total_in_profession=alert.total_in_profession,
            nationality_count=alert.nationality_count,
            detected_date=alert.detected_date,
            is_active=True,
        ))
    
    return CriticalAlertsResponse(
        alerts=alert_details,
        total_count=len(alert_details),
    )


@router.post("/{nationality_code}/refresh", response_model=AlertsResponse)
async def refresh_alerts(
    nationality_code: str,
    db: Session = Depends(get_database)
):
    """
    Refresh dominance alerts for a nationality.
    
    Recalculates all alerts based on current worker distribution.
    """
    nationality = db.query(Nationality).filter(
        Nationality.code == nationality_code.upper()
    ).first()
    
    if not nationality:
        raise HTTPException(status_code=404, detail=f"Nationality {nationality_code} not found")
    
    dominance_engine = DominanceAlertEngine(db)
    
    # Get all alerts (this recalculates them)
    alerts = dominance_engine.get_all_alerts_for_nationality(nationality.id)
    
    # Save/update alerts
    for alert in alerts:
        dominance_engine.save_alert(alert)
    
    # Build response
    alert_details = []
    for alert in alerts:
        alert_details.append(AlertDetailSchema(
            id=0,  # New alert, no ID yet
            nationality_id=alert.nationality_id,
            nationality_code=alert.nationality_code,
            profession_id=alert.profession_id,
            profession_name=alert.profession_name,
            share_pct=alert.share_pct,
            velocity=alert.velocity,
            alert_level=AlertLevelEnum(alert.alert_level.value),
            total_in_profession=alert.total_in_profession,
            nationality_count=alert.nationality_count,
            detected_date=datetime.utcnow(),
            is_active=True,
        ))
    
    return AlertsResponse(
        nationality_id=nationality.id,
        nationality_code=nationality.code,
        alerts=alert_details,
        total_count=len(alert_details),
    )
