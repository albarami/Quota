"""
Queue Management API routes.

Provides endpoints for viewing and managing the auto-queue.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas.models import (
    ConfirmResponse,
    QueueEntrySchema,
    QueueStatusResponse,
    WithdrawResponse,
)
from src.engines import QueueProcessor
from src.models import Nationality, QuotaRequest, get_db

router = APIRouter()


def get_database():
    """Dependency to get database session."""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


@router.get("/{nationality_code}", response_model=QueueStatusResponse)
async def get_queue_status(
    nationality_code: str,
    db: Session = Depends(get_database)
):
    """
    Get queue status for a nationality.
    
    Returns all queued requests grouped by tier.
    """
    nationality = db.query(Nationality).filter(
        Nationality.code == nationality_code.upper()
    ).first()
    
    if not nationality:
        raise HTTPException(status_code=404, detail=f"Nationality {nationality_code} not found")
    
    queue_processor = QueueProcessor(db)
    queue_status = queue_processor.get_queue_status(nationality.id)
    
    # Convert to response format
    by_tier = {}
    total = 0
    
    for tier, entries in queue_status.items():
        by_tier[tier] = [
            QueueEntrySchema(
                queue_id=e.queue_id,
                request_id=e.request_id,
                queue_position=e.queue_position,
                tier_at_submission=e.tier_at_submission,
                queued_date=e.queued_date,
                expiry_date=e.expiry_date,
                days_until_expiry=e.days_until_expiry,
                needs_confirmation=e.needs_confirmation,
                is_confirmed=e.is_confirmed,
            )
            for e in entries
        ]
        total += len(entries)
    
    return QueueStatusResponse(
        nationality_id=nationality.id,
        nationality_code=nationality.code,
        total_queued=total,
        by_tier=by_tier,
    )


@router.post("/{request_id}/withdraw", response_model=WithdrawResponse)
async def withdraw_from_queue(
    request_id: int,
    db: Session = Depends(get_database)
):
    """
    Withdraw a request from the queue.
    
    The request will be marked as withdrawn and removed from the queue.
    """
    # Verify request exists
    request = db.query(QuotaRequest).filter(
        QuotaRequest.id == request_id
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    queue_processor = QueueProcessor(db)
    success = queue_processor.withdraw_from_queue(request_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Request not in queue")
    
    return WithdrawResponse(
        success=True,
        request_id=request_id,
        message="Request withdrawn from queue successfully",
    )


@router.post("/{request_id}/confirm", response_model=ConfirmResponse)
async def confirm_queue_entry(
    request_id: int,
    db: Session = Depends(get_database)
):
    """
    Confirm continued interest in a queued request.
    
    Required after 30 days in queue to prevent expiry.
    """
    # Verify request exists
    request = db.query(QuotaRequest).filter(
        QuotaRequest.id == request_id
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    queue_processor = QueueProcessor(db)
    success = queue_processor.confirm_queue_entry(request_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Request not in queue")
    
    return ConfirmResponse(
        success=True,
        request_id=request_id,
        message="Queue entry confirmed - request will not expire",
    )


@router.post("/{nationality_code}/process", response_model=dict)
async def trigger_queue_processing(
    nationality_code: str,
    tier_level: int = 1,
    db: Session = Depends(get_database)
):
    """
    Manually trigger queue processing for a nationality and tier.
    
    Normally triggered automatically when capacity changes.
    This endpoint is for testing and manual intervention.
    """
    nationality = db.query(Nationality).filter(
        Nationality.code == nationality_code.upper()
    ).first()
    
    if not nationality:
        raise HTTPException(status_code=404, detail=f"Nationality {nationality_code} not found")
    
    if tier_level not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Tier level must be 1-4")
    
    queue_processor = QueueProcessor(db)
    result = queue_processor.process_queue_on_capacity_change(nationality.id, tier_level)
    
    return {
        "nationality_code": nationality_code,
        "tier_level": tier_level,
        "processed_count": result.processed_count,
        "approved_requests": result.approved_requests,
        "remaining_in_queue": result.remaining_in_queue,
        "capacity_used": result.capacity_used,
        "capacity_remaining": result.capacity_remaining,
    }


@router.post("/{nationality_code}/revalidate", response_model=dict)
async def revalidate_queue(
    nationality_code: str,
    db: Session = Depends(get_database)
):
    """
    Revalidate all queued requests for a nationality.
    
    Checks for expired entries, dominance changes, and employer status changes.
    """
    nationality = db.query(Nationality).filter(
        Nationality.code == nationality_code.upper()
    ).first()
    
    if not nationality:
        raise HTTPException(status_code=404, detail=f"Nationality {nationality_code} not found")
    
    queue_processor = QueueProcessor(db)
    valid_entries = queue_processor.revalidate_queue(nationality.id)
    
    return {
        "nationality_code": nationality_code,
        "valid_entries": len(valid_entries),
        "message": f"Queue revalidated - {len(valid_entries)} valid entries remain",
    }
