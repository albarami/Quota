"""
Cap Management API routes.

Provides endpoints for viewing and setting nationality caps.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas.models import (
    CapConfigSchema,
    CapRecommendationSchema,
    SetCapRequest,
    SetCapResponse,
)
from src.engines import AIRecommendationEngine
from src.models import Nationality, NationalityCap, get_db

router = APIRouter()


def get_database():
    """Dependency to get database session."""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[CapConfigSchema])
async def list_caps(
    year: int = None,
    db: Session = Depends(get_database)
):
    """
    List all nationality caps.
    
    Args:
        year: Filter by year (default: current year)
    """
    if year is None:
        year = date.today().year
    
    caps = db.query(NationalityCap).filter(
        NationalityCap.year == year
    ).all()
    
    result = []
    for cap in caps:
        nationality = db.query(Nationality).filter(
            Nationality.id == cap.nationality_id
        ).first()
        
        result.append(CapConfigSchema(
            nationality_id=cap.nationality_id,
            nationality_code=nationality.code if nationality else "UNK",
            year=cap.year,
            cap_limit=cap.cap_limit,
            previous_cap=cap.previous_cap,
            set_by=cap.set_by,
            set_date=cap.set_date,
        ))
    
    return result


@router.get("/{nationality_code}", response_model=CapConfigSchema)
async def get_cap(
    nationality_code: str,
    year: int = None,
    db: Session = Depends(get_database)
):
    """
    Get cap configuration for a specific nationality.
    """
    if year is None:
        year = date.today().year
    
    nationality = db.query(Nationality).filter(
        Nationality.code == nationality_code.upper()
    ).first()
    
    if not nationality:
        raise HTTPException(status_code=404, detail=f"Nationality {nationality_code} not found")
    
    cap = db.query(NationalityCap).filter(
        NationalityCap.nationality_id == nationality.id,
        NationalityCap.year == year
    ).first()
    
    if not cap:
        raise HTTPException(status_code=404, detail=f"No cap set for {nationality_code} in {year}")
    
    return CapConfigSchema(
        nationality_id=cap.nationality_id,
        nationality_code=nationality.code,
        year=cap.year,
        cap_limit=cap.cap_limit,
        previous_cap=cap.previous_cap,
        set_by=cap.set_by,
        set_date=cap.set_date,
    )


@router.get("/{nationality_code}/recommendation", response_model=CapRecommendationSchema)
async def get_cap_recommendation(
    nationality_code: str,
    db: Session = Depends(get_database)
):
    """
    Get AI-powered cap recommendation for a nationality.
    
    Returns conservative, moderate, and flexible options with rationale.
    """
    nationality = db.query(Nationality).filter(
        Nationality.code == nationality_code.upper()
    ).first()
    
    if not nationality:
        raise HTTPException(status_code=404, detail=f"Nationality {nationality_code} not found")
    
    ai_engine = AIRecommendationEngine(db)
    
    try:
        recommendation = ai_engine.generate_cap_recommendation(nationality.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendation: {str(e)}")
    
    return CapRecommendationSchema(
        nationality_id=recommendation.nationality_id,
        nationality_code=recommendation.nationality_code,
        current_stock=recommendation.current_stock,
        current_cap=recommendation.current_cap,
        conservative_cap=recommendation.conservative_cap,
        moderate_cap=recommendation.moderate_cap,
        flexible_cap=recommendation.flexible_cap,
        recommended_cap=recommendation.recommended_cap,
        recommendation_level=recommendation.recommendation_level,
        rationale=recommendation.rationale,
        key_factors=recommendation.key_factors,
        risks=recommendation.risks,
    )


@router.post("/{nationality_code}", response_model=SetCapResponse)
async def set_cap(
    nationality_code: str,
    request: SetCapRequest,
    db: Session = Depends(get_database)
):
    """
    Set cap for a nationality.
    
    Requires Policy Committee authorization (not implemented in demo).
    """
    nationality = db.query(Nationality).filter(
        Nationality.code == nationality_code.upper()
    ).first()
    
    if not nationality:
        raise HTTPException(status_code=404, detail=f"Nationality {nationality_code} not found")
    
    year = date.today().year
    
    # Check for existing cap
    existing = db.query(NationalityCap).filter(
        NationalityCap.nationality_id == nationality.id,
        NationalityCap.year == year
    ).first()
    
    if existing:
        # Update existing cap
        previous = existing.cap_limit
        existing.cap_limit = request.cap_limit
        existing.previous_cap = previous
        existing.set_date = date.today()
        existing.set_by = "API User"  # In production, use authenticated user
        if request.notes:
            existing.notes = request.notes
        message = f"Cap updated from {previous:,} to {request.cap_limit:,}"
    else:
        # Create new cap
        new_cap = NationalityCap(
            nationality_id=nationality.id,
            year=year,
            cap_limit=request.cap_limit,
            set_by="API User",
            set_date=date.today(),
            notes=request.notes,
        )
        db.add(new_cap)
        message = f"New cap set: {request.cap_limit:,}"
    
    db.commit()
    
    return SetCapResponse(
        success=True,
        nationality_id=nationality.id,
        year=year,
        new_cap=request.cap_limit,
        message=message,
    )
