"""
Queue Processor Engine.

Manages the auto-queue for requests waiting for capacity.
Implements the queue lifecycle from Technical Specification Section 12.

Queue Lifecycle:
- Entry: Request queued when tier CLOSED or capacity insufficient
- Revalidation: Re-check eligibility on tier open, dominance change
- Confirmation: Applicant must confirm after 30 days
- Expiry: Request expires after 90 days
- Processing: Priority-weighted FIFO when capacity opens
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from config.settings import ParameterRegistry
from src.engines.capacity import CapacityEngine, TierStatus
from src.engines.dominance import DominanceAlertEngine
from src.models import (
    AlertLevel,
    QuotaRequest,
    RequestQueue,
    RequestStatus,
)


@dataclass
class QueueEntry:
    """Information about a queue entry."""
    
    queue_id: int
    request_id: int
    queue_position: int
    tier_at_submission: int
    queued_date: datetime
    expiry_date: date
    days_until_expiry: int
    needs_confirmation: bool
    is_confirmed: bool
    processing_priority: float


@dataclass
class QueueProcessingResult:
    """Result of processing the queue."""
    
    nationality_id: int
    tier_level: int
    processed_count: int
    approved_requests: list[int]
    remaining_in_queue: int
    capacity_used: int
    capacity_remaining: int


class QueueProcessor:
    """
    Manages the auto-queue for requests waiting for capacity.
    
    The queue is the key innovation of the system - requests are not
    rejected when capacity is unavailable, but queued for automatic
    processing when capacity opens.
    
    Processing order: Priority-Weighted FIFO
    1. Sort by priority score (descending)
    2. Sort by submission timestamp (ascending - older first)
    
    Attributes:
        db: SQLAlchemy database session.
        capacity_engine: CapacityEngine for checking capacity.
        dominance_engine: DominanceAlertEngine for revalidation.
        expiry_days: Days until queue entry expires.
        confirm_days: Days until confirmation required.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the Queue Processor.
        
        Args:
            db: SQLAlchemy database session.
        """
        self.db = db
        self.capacity_engine = CapacityEngine(db)
        self.dominance_engine = DominanceAlertEngine(db)
        self.expiry_days = ParameterRegistry.QUEUE_EXPIRY_DAYS
        self.confirm_days = ParameterRegistry.QUEUE_CONFIRM_DAYS
        self.max_queue_per_tier = ParameterRegistry.MAX_QUEUE_PER_TIER
    
    def add_to_queue(self, request: QuotaRequest) -> QueueEntry:
        """
        Add a request to the queue.
        
        Args:
            request: QuotaRequest to queue.
            
        Returns:
            QueueEntry: Created queue entry.
        """
        # Calculate queue position
        existing_count = self.db.query(func.count(RequestQueue.id)).filter(
            RequestQueue.tier_at_submission == request.tier_at_submission
        ).scalar() or 0
        
        # Check max queue size
        if existing_count >= self.max_queue_per_tier:
            raise ValueError(
                f"Queue for Tier {request.tier_at_submission} is full "
                f"({self.max_queue_per_tier} max)"
            )
        
        # Calculate expiry date
        expiry = date.today() + timedelta(days=self.expiry_days)
        
        # Calculate processing priority (higher = processed first)
        priority = float(request.priority_score) + (
            1.0 / (existing_count + 1)  # Small boost for earlier position
        )
        
        queue_entry = RequestQueue(
            request_id=request.id,
            queue_position=existing_count + 1,
            tier_at_submission=request.tier_at_submission or 2,
            queued_date=datetime.utcnow(),
            expiry_date=expiry,
            processing_priority=priority,
        )
        
        self.db.add(queue_entry)
        self.db.commit()
        
        return QueueEntry(
            queue_id=queue_entry.id,
            request_id=request.id,
            queue_position=queue_entry.queue_position,
            tier_at_submission=queue_entry.tier_at_submission,
            queued_date=queue_entry.queued_date,
            expiry_date=queue_entry.expiry_date,
            days_until_expiry=queue_entry.days_until_expiry,
            needs_confirmation=queue_entry.needs_confirmation,
            is_confirmed=bool(queue_entry.confirmed_date),
            processing_priority=queue_entry.processing_priority,
        )
    
    def process_queue_on_capacity_change(
        self,
        nationality_id: int,
        tier_level: int
    ) -> QueueProcessingResult:
        """
        Process queued requests when capacity becomes available.
        
        Triggered when:
        - Outflow detected (workers depart)
        - Cap adjusted (increased)
        - Tier status changes to OPEN or LIMITED
        
        Args:
            nationality_id: Nationality with capacity change.
            tier_level: Tier level to process.
            
        Returns:
            QueueProcessingResult: Processing results.
        """
        # Get current capacity
        tier_status = self.capacity_engine.calculate_tier_status(nationality_id)
        status = tier_status.tier_statuses.get(tier_level, TierStatus.CLOSED)
        capacity = tier_status.tier_capacities.get(tier_level, 0)
        
        if status == TierStatus.CLOSED or capacity == 0:
            return QueueProcessingResult(
                nationality_id=nationality_id,
                tier_level=tier_level,
                processed_count=0,
                approved_requests=[],
                remaining_in_queue=self._count_queued(nationality_id, tier_level),
                capacity_used=0,
                capacity_remaining=0,
            )
        
        # Get queued requests for this nationality and tier
        queued_requests = self._get_queued_requests(nationality_id, tier_level)
        
        approved_requests = []
        capacity_used = 0
        
        for queue_entry, request in queued_requests:
            # Check if still eligible
            if not self._is_eligible(request):
                continue
            
            # Check capacity
            if capacity_used + request.requested_count > capacity:
                # Check if partial would work
                remaining = capacity - capacity_used
                if remaining >= request.requested_count * 0.5:
                    # Partial approval
                    request.approved_count = remaining
                    request.status = RequestStatus.PARTIAL
                    request.decided_date = datetime.utcnow()
                    request.decision_reason = (
                        f"Auto-approved from queue (partial): "
                        f"{remaining} of {request.requested_count}"
                    )
                    capacity_used += remaining
                    approved_requests.append(request.id)
                    
                    # Remove from queue
                    self.db.delete(queue_entry)
                break
            
            # Full approval
            request.approved_count = request.requested_count
            request.status = RequestStatus.APPROVED
            request.decided_date = datetime.utcnow()
            request.decision_reason = (
                f"Auto-approved from queue: {request.requested_count} workers"
            )
            capacity_used += request.requested_count
            approved_requests.append(request.id)
            
            # Remove from queue
            self.db.delete(queue_entry)
        
        self.db.commit()
        
        # Recalculate remaining
        remaining = self._count_queued(nationality_id, tier_level)
        
        return QueueProcessingResult(
            nationality_id=nationality_id,
            tier_level=tier_level,
            processed_count=len(approved_requests),
            approved_requests=approved_requests,
            remaining_in_queue=remaining,
            capacity_used=capacity_used,
            capacity_remaining=capacity - capacity_used,
        )
    
    def _get_queued_requests(
        self,
        nationality_id: int,
        tier_level: int
    ) -> list[tuple[RequestQueue, QuotaRequest]]:
        """
        Get queued requests sorted by priority-weighted FIFO.
        
        Sort order:
        1. Processing priority (descending)
        2. Queued date (ascending - older first)
        """
        results = self.db.query(RequestQueue, QuotaRequest).join(
            QuotaRequest, RequestQueue.request_id == QuotaRequest.id
        ).filter(
            QuotaRequest.nationality_id == nationality_id,
            RequestQueue.tier_at_submission == tier_level,
            QuotaRequest.status == RequestStatus.QUEUED,
            RequestQueue.expiry_date >= date.today(),
        ).order_by(
            RequestQueue.processing_priority.desc(),
            RequestQueue.queued_date.asc(),
        ).all()
        
        return results
    
    def _count_queued(self, nationality_id: int, tier_level: int) -> int:
        """Count requests in queue for a nationality and tier."""
        return self.db.query(func.count(RequestQueue.id)).join(
            QuotaRequest, RequestQueue.request_id == QuotaRequest.id
        ).filter(
            QuotaRequest.nationality_id == nationality_id,
            RequestQueue.tier_at_submission == tier_level,
            QuotaRequest.status == RequestStatus.QUEUED,
        ).scalar() or 0
    
    def _is_eligible(self, request: QuotaRequest) -> bool:
        """Check if a queued request is still eligible."""
        # Check dominance
        dominance = self.dominance_engine.check_dominance(
            request.nationality_id,
            request.profession_id
        )
        
        if dominance.is_blocking:
            return False
        
        return True
    
    def revalidate_queue(
        self,
        nationality_id: int
    ) -> list[QueueEntry]:
        """
        Revalidate all queued requests for a nationality.
        
        Checks:
        - Expired entries (>90 days)
        - Dominance changes
        - Employer status changes
        
        Args:
            nationality_id: Nationality to revalidate.
            
        Returns:
            List of still-valid queue entries.
        """
        valid_entries = []
        today = date.today()
        
        # Get all queue entries for this nationality
        entries = self.db.query(RequestQueue, QuotaRequest).join(
            QuotaRequest, RequestQueue.request_id == QuotaRequest.id
        ).filter(
            QuotaRequest.nationality_id == nationality_id,
            QuotaRequest.status == RequestStatus.QUEUED,
        ).all()
        
        for queue_entry, request in entries:
            # Check expiry
            if queue_entry.expiry_date < today:
                request.status = RequestStatus.EXPIRED
                request.decision_reason = "Queue entry expired (90 days)"
                self.db.delete(queue_entry)
                continue
            
            # Check dominance
            dominance = self.dominance_engine.check_dominance(
                request.nationality_id,
                request.profession_id
            )
            
            if dominance.is_blocking:
                request.status = RequestStatus.BLOCKED
                request.decision_reason = (
                    f"Blocked during revalidation: dominance {dominance.share_pct:.1%}"
                )
                self.db.delete(queue_entry)
                continue
            
            # Update revalidation timestamp
            queue_entry.last_revalidation = datetime.utcnow()
            
            valid_entries.append(QueueEntry(
                queue_id=queue_entry.id,
                request_id=request.id,
                queue_position=queue_entry.queue_position,
                tier_at_submission=queue_entry.tier_at_submission,
                queued_date=queue_entry.queued_date,
                expiry_date=queue_entry.expiry_date,
                days_until_expiry=queue_entry.days_until_expiry,
                needs_confirmation=queue_entry.needs_confirmation,
                is_confirmed=bool(queue_entry.confirmed_date),
                processing_priority=queue_entry.processing_priority,
            ))
        
        self.db.commit()
        return valid_entries
    
    def get_queue_status(
        self,
        nationality_id: int
    ) -> dict[int, list[QueueEntry]]:
        """
        Get queue status for a nationality grouped by tier.
        
        Args:
            nationality_id: Nationality to check.
            
        Returns:
            Dict mapping tier level to list of queue entries.
        """
        entries = self.db.query(RequestQueue, QuotaRequest).join(
            QuotaRequest, RequestQueue.request_id == QuotaRequest.id
        ).filter(
            QuotaRequest.nationality_id == nationality_id,
            QuotaRequest.status == RequestStatus.QUEUED,
            RequestQueue.expiry_date >= date.today(),
        ).order_by(
            RequestQueue.tier_at_submission,
            RequestQueue.processing_priority.desc(),
        ).all()
        
        result: dict[int, list[QueueEntry]] = {1: [], 2: [], 3: [], 4: []}
        
        for queue_entry, request in entries:
            tier = queue_entry.tier_at_submission
            result[tier].append(QueueEntry(
                queue_id=queue_entry.id,
                request_id=request.id,
                queue_position=queue_entry.queue_position,
                tier_at_submission=tier,
                queued_date=queue_entry.queued_date,
                expiry_date=queue_entry.expiry_date,
                days_until_expiry=queue_entry.days_until_expiry,
                needs_confirmation=queue_entry.needs_confirmation,
                is_confirmed=bool(queue_entry.confirmed_date),
                processing_priority=queue_entry.processing_priority,
            ))
        
        return result
    
    def withdraw_from_queue(self, request_id: int) -> bool:
        """
        Withdraw a request from the queue.
        
        Args:
            request_id: ID of the request to withdraw.
            
        Returns:
            bool: True if withdrawn, False if not found.
        """
        queue_entry = self.db.query(RequestQueue).filter(
            RequestQueue.request_id == request_id
        ).first()
        
        if not queue_entry:
            return False
        
        request = self.db.query(QuotaRequest).filter(
            QuotaRequest.id == request_id
        ).first()
        
        if request:
            request.status = RequestStatus.WITHDRAWN
            request.decision_reason = "Withdrawn by applicant"
            request.decided_date = datetime.utcnow()
        
        self.db.delete(queue_entry)
        self.db.commit()
        
        return True
    
    def confirm_queue_entry(self, request_id: int) -> bool:
        """
        Confirm continued interest in a queued request.
        
        Required after 30 days in queue.
        
        Args:
            request_id: ID of the request to confirm.
            
        Returns:
            bool: True if confirmed, False if not found.
        """
        queue_entry = self.db.query(RequestQueue).filter(
            RequestQueue.request_id == request_id
        ).first()
        
        if not queue_entry:
            return False
        
        queue_entry.confirmed_date = datetime.utcnow()
        self.db.commit()
        
        return True
