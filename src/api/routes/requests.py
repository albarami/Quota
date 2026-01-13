"""
Request Processing API routes.

Provides endpoints for submitting and tracking quota requests.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas.models import (
    DecisionExplanationResponse,
    DecisionResponse,
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    QuotaRequestCreate,
    QuotaRequestResponse,
    RequestStatusEnum,
    DecisionEnum,
    TierStatusEnum,
    AlertLevelEnum,
)
from src.engines import (
    CapacityEngine,
    DominanceAlertEngine,
    RequestProcessor,
    TierDiscoveryEngine,
    QueueProcessor,
    AIRecommendationEngine,
)
from src.models import (
    DecisionLog,
    Establishment,
    Nationality,
    Profession,
    QuotaRequest,
    RequestStatus,
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


@router.post("", response_model=DecisionResponse)
async def submit_request(
    request: QuotaRequestCreate,
    db: Session = Depends(get_database)
):
    """
    Submit a new quota request.
    
    The request is processed immediately through the decision engine.
    Possible outcomes: APPROVED, PARTIAL, QUEUED, BLOCKED, REJECTED
    """
    # Validate establishment
    establishment = db.query(Establishment).filter(
        Establishment.id == request.establishment_id
    ).first()
    if not establishment:
        raise HTTPException(status_code=404, detail="Establishment not found")
    
    # Validate nationality
    nationality = db.query(Nationality).filter(
        Nationality.id == request.nationality_id
    ).first()
    if not nationality:
        raise HTTPException(status_code=404, detail="Nationality not found")
    if not nationality.is_restricted:
        raise HTTPException(status_code=400, detail="Nationality is not restricted")
    
    # Validate profession
    profession = db.query(Profession).filter(
        Profession.id == request.profession_id
    ).first()
    if not profession:
        raise HTTPException(status_code=404, detail="Profession not found")
    
    # Create request record
    quota_request = QuotaRequest(
        establishment_id=request.establishment_id,
        nationality_id=request.nationality_id,
        profession_id=request.profession_id,
        requested_count=request.requested_count,
        status=RequestStatus.SUBMITTED,
        submitted_date=datetime.utcnow(),
    )
    db.add(quota_request)
    db.flush()  # Get ID without committing
    
    # Process request
    processor = RequestProcessor(db)
    decision = processor.process_request(quota_request)
    
    # If queued, add to queue
    if decision.decision.value == "QUEUED":
        queue_processor = QueueProcessor(db)
        queue_processor.add_to_queue(quota_request)
    
    return DecisionResponse(
        request_id=decision.request_id,
        decision=DecisionEnum(decision.decision.value),
        approved_count=decision.approved_count,
        queued_count=decision.queued_count,
        priority_score=decision.priority_score,
        tier_level=decision.tier_level,
        tier_status=TierStatusEnum(decision.tier_status.value),
        dominance_alert=AlertLevelEnum(decision.dominance_alert.value) if decision.dominance_alert else None,
        reason=decision.reason,
        alternatives=decision.alternatives,
    )


@router.post("/check-eligibility", response_model=EligibilityCheckResponse)
async def check_eligibility(
    request: EligibilityCheckRequest,
    db: Session = Depends(get_database)
):
    """
    Check eligibility before submitting a request.
    
    Returns expected outcome without creating a request record.
    Useful for real-time form validation.
    """
    # Validate entities
    nationality = db.query(Nationality).filter(
        Nationality.id == request.nationality_id
    ).first()
    if not nationality or not nationality.is_restricted:
        raise HTTPException(status_code=400, detail="Invalid nationality")
    
    profession = db.query(Profession).filter(
        Profession.id == request.profession_id
    ).first()
    if not profession:
        raise HTTPException(status_code=400, detail="Invalid profession")
    
    establishment = db.query(Establishment).filter(
        Establishment.id == request.establishment_id
    ).first()
    if not establishment:
        raise HTTPException(status_code=400, detail="Invalid establishment")
    
    # Initialize engines
    tier_engine = TierDiscoveryEngine(db)
    capacity_engine = CapacityEngine(db)
    dominance_engine = DominanceAlertEngine(db)
    
    messages = []
    
    # Check tier
    tier_info = tier_engine.get_tier_for_request(
        request.nationality_id,
        request.profession_id
    )
    tier_level = tier_info.tier_level if tier_info else 4
    tier_name = tier_info.tier_name if tier_info else "Unusual"
    
    if tier_level == 4:
        messages.append("This is an unusual profession for this nationality - justification may be required")
    
    # Check tier status
    try:
        tier_status = capacity_engine.calculate_tier_status(request.nationality_id)
        status = tier_status.tier_statuses.get(tier_level, "CLOSED")
        status_value = status.value if hasattr(status, 'value') else status
    except ValueError:
        raise HTTPException(status_code=400, detail="No cap set for this nationality")
    
    if status_value == "CLOSED":
        messages.append("This tier is currently CLOSED - request will be queued")
    elif status_value == "RATIONED":
        messages.append("This tier is RATIONED - priority scoring will be applied")
    elif status_value == "LIMITED":
        messages.append("This tier has LIMITED capacity - partial approval possible")
    
    # Check dominance
    dominance = dominance_engine.check_dominance(
        request.nationality_id,
        request.profession_id
    )
    
    if dominance.is_blocking:
        messages.append(f"CRITICAL: This nationality has {dominance.share_pct:.1%} share - approvals blocked")
    elif dominance.is_partial_only:
        messages.append(f"HIGH: This nationality has {dominance.share_pct:.1%} share - partial approval only")
    elif dominance.requires_review:
        messages.append(f"WATCH: This nationality has {dominance.share_pct:.1%} share - flagged for review")
    
    # Calculate priority score (mock request)
    mock_request = QuotaRequest(
        establishment_id=request.establishment_id,
        nationality_id=request.nationality_id,
        profession_id=request.profession_id,
        requested_count=request.requested_count,
    )
    processor = RequestProcessor(db)
    priority_score = processor.calculate_priority_score(mock_request)
    
    # Determine estimated outcome
    if dominance.is_blocking:
        estimated = DecisionEnum.BLOCKED
        is_eligible = False
    elif status_value == "CLOSED":
        estimated = DecisionEnum.QUEUED
        is_eligible = True
    elif status_value in ["LIMITED", "RATIONED"] and dominance.is_partial_only:
        estimated = DecisionEnum.PARTIAL
        is_eligible = True
    elif status_value == "OPEN" and not dominance.is_partial_only:
        estimated = DecisionEnum.APPROVED
        is_eligible = True
    else:
        estimated = DecisionEnum.PARTIAL
        is_eligible = True
    
    return EligibilityCheckResponse(
        is_eligible=is_eligible,
        tier_level=tier_level,
        tier_name=tier_name,
        tier_status=TierStatusEnum(status_value),
        dominance_alert=AlertLevelEnum(dominance.alert_level.value) if dominance.alert_level else None,
        estimated_outcome=estimated,
        priority_score=priority_score,
        messages=messages,
    )


@router.get("/{request_id}", response_model=QuotaRequestResponse)
async def get_request(
    request_id: int,
    db: Session = Depends(get_database)
):
    """
    Get details of a specific request.
    """
    request = db.query(QuotaRequest).filter(
        QuotaRequest.id == request_id
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    nationality = db.query(Nationality).filter(
        Nationality.id == request.nationality_id
    ).first()
    profession = db.query(Profession).filter(
        Profession.id == request.profession_id
    ).first()
    
    return QuotaRequestResponse(
        id=request.id,
        establishment_id=request.establishment_id,
        nationality_id=request.nationality_id,
        nationality_code=nationality.code if nationality else "UNK",
        profession_id=request.profession_id,
        profession_name=profession.name if profession else "Unknown",
        requested_count=request.requested_count,
        approved_count=request.approved_count,
        status=RequestStatusEnum(request.status.value),
        priority_score=request.priority_score,
        tier_at_submission=request.tier_at_submission,
        submitted_date=request.submitted_date,
        decided_date=request.decided_date,
        decision_reason=request.decision_reason,
    )


@router.get("/{request_id}/explain", response_model=DecisionExplanationResponse)
async def explain_decision(
    request_id: int,
    db: Session = Depends(get_database)
):
    """
    Get AI-generated explanation for a request decision.
    """
    # Get decision log
    decision_log = db.query(DecisionLog).filter(
        DecisionLog.request_id == request_id
    ).order_by(DecisionLog.decision_timestamp.desc()).first()
    
    if not decision_log:
        raise HTTPException(status_code=404, detail="No decision log found for this request")
    
    ai_engine = AIRecommendationEngine(db)
    explanation = ai_engine.explain_decision(decision_log)
    
    return DecisionExplanationResponse(
        request_id=explanation.request_id,
        decision=explanation.decision,
        summary=explanation.summary,
        detailed_explanation=explanation.detailed_explanation,
        factors_considered=explanation.factors_considered,
        next_steps=explanation.next_steps,
    )
