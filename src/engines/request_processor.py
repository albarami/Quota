"""
Request Processor Engine.

Main decision engine that processes quota requests through all checks.
Implements the decision flow from Technical Specification Section 6.1.

Decision Flow:
1. Identify Tier for nationality-profession
2. Check Tier Status (OPEN/RATIONED/LIMITED/CLOSED)
3. If tier available, check Dominance Alert
4. Calculate Priority Score
5. Make decision: APPROVE / PARTIAL / QUEUE / BLOCK / REJECT
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from config.settings import ParameterRegistry
from src.engines.capacity import CapacityEngine, TierStatus
from src.engines.dominance import DominanceAlertEngine
from src.engines.tier_discovery import TierDiscoveryEngine
from src.models import (
    AlertLevel,
    DecisionLog,
    DecisionType,
    EconomicActivity,
    Establishment,
    Profession,
    QuotaRequest,
    RequestStatus,
)


@dataclass
class Decision:
    """Result of request processing."""
    
    request_id: int
    decision: DecisionType
    approved_count: int
    queued_count: int
    priority_score: int
    tier_level: int
    tier_status: TierStatus
    dominance_alert: Optional[AlertLevel]
    reason: str
    alternatives: list[str]
    rule_chain: list[dict]


class RequestProcessor:
    """
    Main decision engine for quota requests.
    
    Processes requests through the complete decision flow:
    1. Tier identification
    2. Tier status check
    3. Dominance check
    4. Priority scoring
    5. Decision making
    
    All decisions are logged to DecisionLog for audit.
    
    Attributes:
        db: SQLAlchemy database session.
        tier_engine: TierDiscoveryEngine instance.
        capacity_engine: CapacityEngine instance.
        dominance_engine: DominanceAlertEngine instance.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the Request Processor.
        
        Args:
            db: SQLAlchemy database session.
        """
        self.db = db
        self.tier_engine = TierDiscoveryEngine(db)
        self.capacity_engine = CapacityEngine(db)
        self.dominance_engine = DominanceAlertEngine(db)
    
    def process_request(self, request: QuotaRequest) -> Decision:
        """
        Process a quota request through the complete decision flow.
        
        Args:
            request: QuotaRequest to process.
            
        Returns:
            Decision: Complete decision with rationale.
        """
        rule_chain = []
        alternatives = []
        
        # Step 1: Get tier classification
        tier_info = self.tier_engine.get_tier_for_request(
            request.nationality_id,
            request.profession_id
        )
        
        if tier_info:
            tier_level = tier_info.tier_level
            rule_chain.append({
                "rule": "tier_identification",
                "result": f"Tier {tier_level} ({tier_info.tier_name})",
                "share": tier_info.share_pct,
            })
        else:
            # No tier classification - treat as Tier 4 (Unusual)
            tier_level = 4
            rule_chain.append({
                "rule": "tier_identification",
                "result": "Tier 4 (Unusual - no historical pattern)",
                "share": 0.0,
            })
        
        # Step 2: Check tier status
        tier_status_result = self.capacity_engine.calculate_tier_status(
            request.nationality_id
        )
        tier_status = tier_status_result.tier_statuses.get(tier_level, TierStatus.CLOSED)
        tier_capacity = tier_status_result.tier_capacities.get(tier_level, 0)
        
        rule_chain.append({
            "rule": "tier_status_check",
            "result": tier_status.value,
            "capacity": tier_capacity,
            "headroom": tier_status_result.headroom,
        })
        
        # Step 3: Check dominance
        dominance_result = self.dominance_engine.check_dominance(
            request.nationality_id,
            request.profession_id
        )
        
        rule_chain.append({
            "rule": "dominance_check",
            "result": dominance_result.alert_level.value,
            "share": dominance_result.share_pct,
            "velocity": dominance_result.velocity,
            "is_blocking": dominance_result.is_blocking,
        })
        
        # Step 4: Calculate priority score
        priority_score = self.calculate_priority_score(request)
        
        rule_chain.append({
            "rule": "priority_scoring",
            "result": priority_score,
        })
        
        # Step 5: Make decision
        decision, approved_count, queued_count, reason = self._make_decision(
            request=request,
            tier_level=tier_level,
            tier_status=tier_status,
            tier_capacity=tier_capacity,
            dominance_result=dominance_result,
            priority_score=priority_score,
            rule_chain=rule_chain,
            alternatives=alternatives,
        )
        
        # Update request
        request.status = self._decision_to_status(decision)
        request.approved_count = approved_count
        request.priority_score = priority_score
        request.tier_at_submission = tier_level
        request.decided_date = datetime.utcnow()
        request.decision_reason = reason
        
        # Log decision
        self._log_decision(
            request=request,
            decision=decision,
            tier_status_result=tier_status_result,
            dominance_result=dominance_result,
            priority_score=priority_score,
            rule_chain=rule_chain,
        )
        
        self.db.commit()
        
        return Decision(
            request_id=request.id,
            decision=decision,
            approved_count=approved_count,
            queued_count=queued_count,
            priority_score=priority_score,
            tier_level=tier_level,
            tier_status=tier_status,
            dominance_alert=dominance_result.alert_level,
            reason=reason,
            alternatives=alternatives,
            rule_chain=rule_chain,
        )
    
    def _make_decision(
        self,
        request: QuotaRequest,
        tier_level: int,
        tier_status: TierStatus,
        tier_capacity: int,
        dominance_result,
        priority_score: int,
        rule_chain: list,
        alternatives: list,
    ) -> tuple[DecisionType, int, int, str]:
        """
        Make the final decision based on all checks.
        
        Returns:
            Tuple of (decision, approved_count, queued_count, reason)
        """
        requested = request.requested_count
        
        # Check for dominance blocking first
        if dominance_result.is_blocking:
            # Add alternatives
            alternatives.extend(self._find_alternatives(request))
            reason = (
                f"BLOCKED: {dominance_result.nationality_code} dominance in "
                f"{dominance_result.profession_name} is {dominance_result.share_pct:.1%} "
                f"(CRITICAL). Diversification required."
            )
            rule_chain.append({
                "rule": "dominance_block",
                "result": "BLOCKED",
                "reason": reason,
            })
            return DecisionType.BLOCKED, 0, 0, reason
        
        # Check tier status
        if tier_status == TierStatus.OPEN:
            # Check dominance partial requirement
            if dominance_result.is_partial_only:
                # Approve 50% maximum
                approved = min(requested, requested // 2)
                reason = (
                    f"PARTIAL: Tier {tier_level} OPEN but dominance HIGH "
                    f"({dominance_result.share_pct:.1%}). "
                    f"Approved {approved} of {requested}."
                )
                rule_chain.append({
                    "rule": "dominance_partial",
                    "result": "PARTIAL",
                    "approved": approved,
                })
                return DecisionType.PARTIAL, approved, 0, reason
            else:
                # Full approval
                reason = (
                    f"APPROVED: Tier {tier_level} OPEN, "
                    f"dominance OK ({dominance_result.share_pct:.1%}). "
                    f"All {requested} workers approved."
                )
                rule_chain.append({
                    "rule": "tier_open_approval",
                    "result": "APPROVED",
                    "approved": requested,
                })
                return DecisionType.APPROVED, requested, 0, reason
        
        elif tier_status == TierStatus.RATIONED:
            # Limited capacity - use priority scoring
            if tier_capacity >= requested:
                # Can fulfill full request
                reason = (
                    f"APPROVED: Tier {tier_level} RATIONED but capacity sufficient. "
                    f"Priority score: {priority_score}. Approved {requested}."
                )
                rule_chain.append({
                    "rule": "rationed_sufficient",
                    "result": "APPROVED",
                    "approved": requested,
                })
                return DecisionType.APPROVED, requested, 0, reason
            elif tier_capacity >= requested * 0.5:
                # Partial approval
                approved = tier_capacity
                reason = (
                    f"PARTIAL: Tier {tier_level} RATIONED. "
                    f"Capacity {tier_capacity}, requested {requested}. "
                    f"Priority: {priority_score}. Approved {approved}."
                )
                rule_chain.append({
                    "rule": "rationed_partial",
                    "result": "PARTIAL",
                    "approved": approved,
                })
                return DecisionType.PARTIAL, approved, 0, reason
            else:
                # Queue entire request
                reason = (
                    f"QUEUED: Tier {tier_level} RATIONED. "
                    f"Capacity {tier_capacity} insufficient for {requested}. "
                    f"Request queued for auto-processing."
                )
                rule_chain.append({
                    "rule": "rationed_queue",
                    "result": "QUEUED",
                    "queued": requested,
                })
                return DecisionType.QUEUED, 0, requested, reason
        
        elif tier_status == TierStatus.LIMITED:
            # Very limited - partial or queue
            if tier_capacity > 0 and tier_capacity >= requested * 0.5:
                approved = tier_capacity
                reason = (
                    f"PARTIAL: Tier {tier_level} LIMITED. "
                    f"Only {tier_capacity} slots available. "
                    f"Approved {approved}, remainder can be queued."
                )
                rule_chain.append({
                    "rule": "limited_partial",
                    "result": "PARTIAL",
                    "approved": approved,
                })
                return DecisionType.PARTIAL, approved, 0, reason
            else:
                # Queue
                reason = (
                    f"QUEUED: Tier {tier_level} LIMITED. "
                    f"Insufficient capacity. Request queued."
                )
                rule_chain.append({
                    "rule": "limited_queue",
                    "result": "QUEUED",
                    "queued": requested,
                })
                return DecisionType.QUEUED, 0, requested, reason
        
        else:  # CLOSED
            # Queue or reject based on tier
            if tier_level <= 3:
                # Tier 1-3: Queue for auto-processing
                reason = (
                    f"QUEUED: Tier {tier_level} CLOSED. "
                    f"Request queued for auto-processing when capacity opens."
                )
                rule_chain.append({
                    "rule": "closed_queue",
                    "result": "QUEUED",
                    "queued": requested,
                })
                return DecisionType.QUEUED, 0, requested, reason
            else:
                # Tier 4 (Unusual): Requires justification
                reason = (
                    f"REJECTED: Tier 4 (Unusual) request when capacity closed. "
                    f"Business justification required for unusual profession requests."
                )
                rule_chain.append({
                    "rule": "unusual_rejected",
                    "result": "REJECTED",
                })
                return DecisionType.REJECTED, 0, 0, reason
    
    def _decision_to_status(self, decision: DecisionType) -> RequestStatus:
        """Convert decision type to request status."""
        mapping = {
            DecisionType.APPROVED: RequestStatus.APPROVED,
            DecisionType.PARTIAL: RequestStatus.PARTIAL,
            DecisionType.QUEUED: RequestStatus.QUEUED,
            DecisionType.BLOCKED: RequestStatus.BLOCKED,
            DecisionType.REJECTED: RequestStatus.REJECTED,
        }
        return mapping.get(decision, RequestStatus.REJECTED)
    
    def _find_alternatives(self, request: QuotaRequest) -> list[str]:
        """Find alternative nationalities for a blocked request."""
        # Get profession info
        profession = self.db.query(Profession).filter(
            Profession.id == request.profession_id
        ).first()
        
        if not profession:
            return []
        
        # Find nationalities with low dominance in this profession
        # (simplified - in production would check actual availability)
        return [
            f"Consider Indian workers (typical share: 18%)",
            f"Consider Nepali workers (typical share: 7%)",
            f"Consider Pakistani workers (typical share: 9%)",
        ]
    
    def calculate_priority_score(self, request: QuotaRequest) -> int:
        """
        Calculate priority score for a request.
        
        From spec Section 11.1:
        - HIGH_DEMAND_SKILL_FLAG: +50 points
        - Strategic Sector: +30 points
        - Utilization >90%: +20 points
        - Utilization 70-90%: +10 points
        - Utilization <30%: -20 points
        - Small Establishment: +10 points
        
        Args:
            request: QuotaRequest to score.
            
        Returns:
            int: Priority score.
        """
        score = 0
        
        # Get profession
        profession = self.db.query(Profession).filter(
            Profession.id == request.profession_id
        ).first()
        
        if profession and profession.high_demand_flag:
            score += ParameterRegistry.PRIORITY_HIGH_DEMAND_SKILL
        
        # Get establishment
        establishment = self.db.query(Establishment).filter(
            Establishment.id == request.establishment_id
        ).first()
        
        if establishment:
            # Check strategic sector
            if establishment.activity_id:
                activity = self.db.query(EconomicActivity).filter(
                    EconomicActivity.id == establishment.activity_id
                ).first()
                if activity and activity.is_strategic:
                    score += ParameterRegistry.PRIORITY_STRATEGIC_SECTOR
            
            # Check utilization
            util = establishment.utilization_rate
            if util >= ParameterRegistry.UTILIZATION_HIGH:
                score += ParameterRegistry.PRIORITY_HIGH_UTILIZATION
            elif util >= ParameterRegistry.UTILIZATION_MEDIUM:
                score += ParameterRegistry.PRIORITY_MEDIUM_UTILIZATION
            elif util < ParameterRegistry.UTILIZATION_LOW:
                score += ParameterRegistry.PRIORITY_LOW_UTILIZATION
            
            # Check small establishment
            if establishment.is_small:
                score += ParameterRegistry.PRIORITY_SMALL_ESTABLISHMENT
        
        return score
    
    def _log_decision(
        self,
        request: QuotaRequest,
        decision: DecisionType,
        tier_status_result,
        dominance_result,
        priority_score: int,
        rule_chain: list,
    ) -> None:
        """Log decision to DecisionLog for audit."""
        log = DecisionLog(
            request_id=request.id,
            decision=decision,
            tier_status_snapshot=json.dumps({
                k: v.value for k, v in tier_status_result.tier_statuses.items()
            }),
            capacity_snapshot=json.dumps(
                self.capacity_engine.get_capacity_snapshot(request.nationality_id)
            ),
            dominance_snapshot=json.dumps(
                self.dominance_engine.get_dominance_snapshot(
                    request.nationality_id, request.profession_id
                )
            ),
            priority_score=priority_score,
            rule_chain=json.dumps(rule_chain),
            parameter_version="v2.0",
            override_flag=0,
            decision_timestamp=datetime.utcnow(),
        )
        self.db.add(log)
