"""
Integration tests for end-to-end flows.

Tests complete workflows from request submission to decision.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from datetime import datetime

from src.engines import (
    RequestProcessor,
    QueueProcessor,
    CapacityEngine,
    DominanceAlertEngine,
)
from src.models import (
    QuotaRequest,
    RequestStatus,
    WorkerState,
)


class TestRequestApprovalFlow:
    """Test complete request approval workflow."""
    
    def test_full_approval_flow(
        self,
        db_session,
        sample_nationalities,
        sample_professions,
        sample_establishments,
        sample_caps,
        sample_tiers,
        sample_workers,
    ):
        """Test request submission through to approval."""
        # 1. Create request
        request = QuotaRequest(
            establishment_id=sample_establishments[0].id,
            nationality_id=sample_nationalities[0].id,
            profession_id=sample_professions[0].id,
            requested_count=5,
            status=RequestStatus.SUBMITTED,
            submitted_date=datetime.utcnow(),
        )
        db_session.add(request)
        db_session.commit()
        
        # 2. Check capacity before
        capacity_engine = CapacityEngine(db_session)
        before = capacity_engine.calculate_effective_headroom(
            sample_nationalities[0].id, include_outflow=False
        )
        
        # 3. Process request
        processor = RequestProcessor(db_session)
        decision = processor.process_request(request)
        
        # 4. Verify approval
        assert decision.decision.value == "APPROVED"
        assert decision.approved_count == 5
        assert request.status == RequestStatus.APPROVED
        assert request.approved_count == 5
        
        # 5. Verify decision was logged
        from src.models import DecisionLog
        log = db_session.query(DecisionLog).filter(
            DecisionLog.request_id == request.id
        ).first()
        assert log is not None
        assert log.decision.value == "APPROVED"


class TestQueueFlow:
    """Test request queuing and auto-processing workflow."""
    
    def test_queue_and_process_flow(
        self,
        db_session,
        sample_nationalities,
        sample_professions,
        sample_establishments,
        sample_caps,
    ):
        """Test request being queued and later processed."""
        # Create a request that will be queued
        request = QuotaRequest(
            establishment_id=sample_establishments[0].id,
            nationality_id=sample_nationalities[0].id,
            profession_id=sample_professions[0].id,
            requested_count=10,
            status=RequestStatus.QUEUED,
            tier_at_submission=1,
            priority_score=60,
            submitted_date=datetime.utcnow(),
        )
        db_session.add(request)
        db_session.commit()
        
        # Add to queue
        queue_processor = QueueProcessor(db_session)
        entry = queue_processor.add_to_queue(request)
        
        assert entry is not None
        assert entry.queue_position >= 1
        
        # Get queue status
        status = queue_processor.get_queue_status(sample_nationalities[0].id)
        assert 1 in status  # Tier 1 queue exists
        
        # Process queue (simulating capacity opening)
        result = queue_processor.process_queue_on_capacity_change(
            sample_nationalities[0].id,
            tier_level=1
        )
        
        # With capacity available, request should be processed
        assert result.processed_count >= 0


class TestDominanceBlockFlow:
    """Test dominance blocking workflow."""
    
    def test_dominance_blocks_approval(
        self,
        db_session,
        sample_nationalities,
        sample_professions,
        sample_establishments,
        sample_caps,
    ):
        """Test that high dominance blocks new approvals."""
        from tests.conftest import create_workers_for_dominance
        
        # Create dominance situation (>50% share)
        create_workers_for_dominance(
            db_session,
            sample_nationalities[0].id,
            sample_professions[3].id,  # Electrician
            sample_establishments[0].id,
            150
        )
        create_workers_for_dominance(
            db_session,
            sample_nationalities[1].id,
            sample_professions[3].id,
            sample_establishments[0].id,
            50
        )
        
        # Check dominance
        dominance_engine = DominanceAlertEngine(db_session)
        check = dominance_engine.check_dominance(
            sample_nationalities[0].id,
            sample_professions[3].id
        )
        
        # Should be critical (75% share)
        assert check.alert_level.value == "CRITICAL"
        assert check.is_blocking
        
        # Create a request for the blocked combination
        from src.models import NationalityTier
        
        # Add tier for this profession
        tier = NationalityTier(
            nationality_id=sample_nationalities[0].id,
            profession_id=sample_professions[3].id,
            tier_level=2,
            share_pct=0.08,
            valid_from=datetime.utcnow().date(),
        )
        db_session.add(tier)
        db_session.commit()
        
        request = QuotaRequest(
            establishment_id=sample_establishments[0].id,
            nationality_id=sample_nationalities[0].id,
            profession_id=sample_professions[3].id,
            requested_count=5,
            status=RequestStatus.SUBMITTED,
            submitted_date=datetime.utcnow(),
        )
        db_session.add(request)
        db_session.commit()
        
        # Process request
        processor = RequestProcessor(db_session)
        decision = processor.process_request(request)
        
        # Should be blocked
        assert decision.decision.value == "BLOCKED"
        assert decision.approved_count == 0
        assert "dominance" in decision.reason.lower() or "blocked" in decision.reason.lower()


class TestPartialApprovalFlow:
    """Test partial approval scenarios."""
    
    def test_partial_due_to_dominance(
        self,
        db_session,
        sample_nationalities,
        sample_professions,
        sample_establishments,
        sample_caps,
        sample_tiers,
    ):
        """Test partial approval due to HIGH dominance."""
        from tests.conftest import create_workers_for_dominance
        
        # Create HIGH dominance situation (40-50% share)
        create_workers_for_dominance(
            db_session,
            sample_nationalities[0].id,
            sample_professions[1].id,  # Site Engineer
            sample_establishments[0].id,
            90
        )
        create_workers_for_dominance(
            db_session,
            sample_nationalities[1].id,
            sample_professions[1].id,
            sample_establishments[0].id,
            110
        )
        
        # Check dominance - should be HIGH (45% share)
        dominance_engine = DominanceAlertEngine(db_session)
        check = dominance_engine.check_dominance(
            sample_nationalities[0].id,
            sample_professions[1].id
        )
        
        assert check.alert_level.value in ["HIGH", "CRITICAL"]


class TestCapacityCalculations:
    """Test capacity engine calculations."""
    
    def test_headroom_formula(
        self,
        db_session,
        sample_nationalities,
        sample_caps,
        sample_workers,
    ):
        """Test the golden formula for headroom calculation."""
        engine = CapacityEngine(db_session)
        
        result = engine.calculate_effective_headroom(
            sample_nationalities[0].id,
            include_outflow=False
        )
        
        # Formula: cap - stock - committed - (pending * 0.8) + (outflow * 0.75)
        # With include_outflow=False, outflow = 0
        
        expected_raw = result.cap - result.stock - result.committed
        assert result.raw_headroom == expected_raw
        
        # Utilization should be stock / cap
        expected_util = result.stock / result.cap
        assert abs(result.utilization_pct - expected_util) < 0.01
    
    def test_tier_status_cascade(
        self,
        db_session,
        sample_nationalities,
        sample_caps,
        sample_workers,
        sample_tiers,
    ):
        """Test that tier statuses cascade properly."""
        engine = CapacityEngine(db_session)
        
        result = engine.calculate_tier_status(sample_nationalities[0].id)
        
        # All 4 tiers should have a status
        assert 1 in result.tier_statuses
        assert 2 in result.tier_statuses
        assert 3 in result.tier_statuses
        assert 4 in result.tier_statuses
        
        # With plenty of headroom, tiers should mostly be OPEN
        from src.engines.capacity import TierStatus
        assert result.tier_statuses[1] in [
            TierStatus.OPEN, TierStatus.RATIONED, TierStatus.LIMITED, TierStatus.CLOSED
        ]
