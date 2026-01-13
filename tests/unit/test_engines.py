"""
Unit tests for business logic engines.

Tests the core engines: TierDiscovery, Capacity, Dominance, RequestProcessor.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from datetime import date, datetime, timedelta

from src.engines import (
    TierDiscoveryEngine,
    CapacityEngine,
    DominanceAlertEngine,
    RequestProcessor,
    QueueProcessor,
    TierStatus,
)
from src.models import (
    NationalityTier,
    QuotaRequest,
    RequestStatus,
    WorkerStock,
    WorkerState,
    AlertLevel,
)


class TestTierDiscoveryEngine:
    """Tests for TierDiscoveryEngine."""
    
    def test_get_tier_for_request_existing(
        self,
        db_session,
        sample_nationalities,
        sample_professions,
        sample_tiers,
    ):
        """Test getting existing tier classification."""
        engine = TierDiscoveryEngine(db_session)
        
        # Egypt + Construction Supervisor should be Tier 1
        tier_info = engine.get_tier_for_request(
            sample_nationalities[0].id,
            sample_professions[0].id
        )
        
        assert tier_info is not None
        assert tier_info.tier_level == 1
        assert tier_info.tier_name == "Primary"
        assert tier_info.share_pct == 0.33
    
    def test_get_tier_for_request_missing(
        self,
        db_session,
        sample_nationalities,
        sample_professions,
    ):
        """Test getting tier for unclassified profession."""
        engine = TierDiscoveryEngine(db_session)
        
        # Egypt + Plumber has no tier classification
        tier_info = engine.get_tier_for_request(
            sample_nationalities[0].id,
            sample_professions[4].id  # Plumber
        )
        
        assert tier_info is None
    
    def test_tier_name_mapping(self, db_session):
        """Test tier level to name mapping."""
        engine = TierDiscoveryEngine(db_session)
        
        assert engine._tier_name(1) == "Primary"
        assert engine._tier_name(2) == "Secondary"
        assert engine._tier_name(3) == "Minor"
        assert engine._tier_name(4) == "Unusual"


class TestCapacityEngine:
    """Tests for CapacityEngine."""
    
    def test_calculate_effective_headroom(
        self,
        db_session,
        sample_nationalities,
        sample_caps,
        sample_workers,
    ):
        """Test headroom calculation."""
        engine = CapacityEngine(db_session)
        
        result = engine.calculate_effective_headroom(
            sample_nationalities[0].id,  # Egypt
            include_outflow=False
        )
        
        assert result.cap == 15000
        assert result.stock == 150  # 100 + 50 workers from fixture
        assert result.raw_headroom == 15000 - 150
    
    def test_calculate_tier_status(
        self,
        db_session,
        sample_nationalities,
        sample_caps,
        sample_workers,
        sample_tiers,
    ):
        """Test tier status calculation."""
        engine = CapacityEngine(db_session)
        
        result = engine.calculate_tier_status(sample_nationalities[0].id)
        
        # With plenty of headroom, all tiers should be OPEN
        assert result.tier_statuses[1] == TierStatus.OPEN
        assert result.headroom > 0
    
    def test_missing_cap_raises_error(
        self,
        db_session,
        sample_nationalities,
    ):
        """Test that missing cap raises ValueError."""
        engine = CapacityEngine(db_session)
        
        # Nepal has no cap set
        with pytest.raises(ValueError, match="No cap set"):
            engine.calculate_effective_headroom(sample_nationalities[3].id)


class TestDominanceAlertEngine:
    """Tests for DominanceAlertEngine."""
    
    def test_check_dominance_ok(
        self,
        db_session,
        sample_nationalities,
        sample_professions,
        sample_workers,
        sample_establishments,
    ):
        """Test dominance check when below threshold."""
        # Add workers from other nationalities to lower Egypt's share
        from tests.conftest import create_workers_for_dominance
        
        # Add 200 workers from Bangladesh
        create_workers_for_dominance(
            db_session,
            sample_nationalities[1].id,  # Bangladesh
            sample_professions[0].id,
            sample_establishments[0].id,
            200
        )
        
        engine = DominanceAlertEngine(db_session)
        result = engine.check_dominance(
            sample_nationalities[0].id,
            sample_professions[0].id
        )
        
        # 100 Egyptian out of 300 = 33% (below 40% WATCH threshold)
        # But profession size is 300 which is > MIN_PROFESSION_SIZE (200)
        assert result.alert_level in [AlertLevel.OK, AlertLevel.WATCH]
        assert not result.is_blocking
    
    def test_check_dominance_critical(
        self,
        db_session,
        sample_nationalities,
        sample_professions,
        sample_establishments,
    ):
        """Test dominance check when above critical threshold."""
        from tests.conftest import create_workers_for_dominance
        
        # Create 150 Egyptian workers (dominant)
        create_workers_for_dominance(
            db_session,
            sample_nationalities[0].id,
            sample_professions[2].id,  # General Labourer
            sample_establishments[0].id,
            150
        )
        
        # Create 50 workers from other nationality
        create_workers_for_dominance(
            db_session,
            sample_nationalities[1].id,
            sample_professions[2].id,
            sample_establishments[0].id,
            50
        )
        
        engine = DominanceAlertEngine(db_session)
        result = engine.check_dominance(
            sample_nationalities[0].id,
            sample_professions[2].id
        )
        
        # 150 out of 200 = 75% (above 50% CRITICAL threshold)
        assert result.alert_level == AlertLevel.CRITICAL
        assert result.is_blocking


class TestRequestProcessor:
    """Tests for RequestProcessor."""
    
    def test_calculate_priority_score(
        self,
        db_session,
        sample_request,
        sample_professions,
        sample_establishments,
    ):
        """Test priority score calculation."""
        processor = RequestProcessor(db_session)
        score = processor.calculate_priority_score(sample_request)
        
        # Should get points for:
        # - high_demand_flag (+50)
        # - strategic sector (+30)
        # - utilization 85% (+10)
        assert score > 0
    
    def test_process_request_approved(
        self,
        db_session,
        sample_nationalities,
        sample_professions,
        sample_establishments,
        sample_caps,
        sample_tiers,
        sample_workers,
    ):
        """Test processing a request that should be approved."""
        # Create a fresh request
        request = QuotaRequest(
            establishment_id=sample_establishments[0].id,
            nationality_id=sample_nationalities[0].id,
            profession_id=sample_professions[0].id,  # Tier 1
            requested_count=5,
            status=RequestStatus.SUBMITTED,
            submitted_date=datetime.utcnow(),
        )
        db_session.add(request)
        db_session.commit()
        
        processor = RequestProcessor(db_session)
        decision = processor.process_request(request)
        
        # With plenty of headroom and Tier 1 open
        assert decision.approved_count == 5
        assert request.status == RequestStatus.APPROVED


class TestQueueProcessor:
    """Tests for QueueProcessor."""
    
    def test_add_to_queue(
        self,
        db_session,
        sample_nationalities,
        sample_professions,
        sample_establishments,
        sample_caps,
    ):
        """Test adding a request to the queue."""
        # Create a request
        request = QuotaRequest(
            establishment_id=sample_establishments[0].id,
            nationality_id=sample_nationalities[0].id,
            profession_id=sample_professions[0].id,
            requested_count=10,
            status=RequestStatus.QUEUED,
            tier_at_submission=1,
            priority_score=50,
            submitted_date=datetime.utcnow(),
        )
        db_session.add(request)
        db_session.commit()
        
        processor = QueueProcessor(db_session)
        entry = processor.add_to_queue(request)
        
        assert entry.request_id == request.id
        assert entry.queue_position == 1
        assert entry.days_until_expiry <= 90
    
    def test_withdraw_from_queue(
        self,
        db_session,
        sample_nationalities,
        sample_professions,
        sample_establishments,
        sample_caps,
    ):
        """Test withdrawing a request from the queue."""
        # Create and queue a request
        request = QuotaRequest(
            establishment_id=sample_establishments[0].id,
            nationality_id=sample_nationalities[0].id,
            profession_id=sample_professions[0].id,
            requested_count=10,
            status=RequestStatus.QUEUED,
            tier_at_submission=1,
            priority_score=50,
            submitted_date=datetime.utcnow(),
        )
        db_session.add(request)
        db_session.commit()
        
        processor = QueueProcessor(db_session)
        processor.add_to_queue(request)
        
        # Withdraw
        success = processor.withdraw_from_queue(request.id)
        
        assert success
        assert request.status == RequestStatus.WITHDRAWN
