"""
AI Recommendation Engine.

Uses Azure OpenAI to provide intelligent interpretations and recommendations.
Generates human-readable explanations and strategic insights.

Features:
- Cap recommendations with rationale
- Decision explanations
- Market trend analysis
- Alternative suggestions
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from config.settings import get_settings
from src.engines.capacity import CapacityEngine
from src.engines.dominance import DominanceAlertEngine
from src.models import (
    DecisionLog,
    Nationality,
    NationalityCap,
    QuotaRequest,
)


@dataclass
class CapRecommendation:
    """AI-generated cap recommendation."""
    
    nationality_id: int
    nationality_code: str
    current_stock: int
    current_cap: Optional[int]
    conservative_cap: int
    moderate_cap: int
    flexible_cap: int
    recommended_cap: int
    recommendation_level: str  # "conservative", "moderate", "flexible"
    rationale: str
    key_factors: list[str]
    risks: list[str]
    generated_at: datetime


@dataclass
class DecisionExplanation:
    """AI-generated explanation of a decision."""
    
    request_id: int
    decision: str
    summary: str
    detailed_explanation: str
    factors_considered: list[str]
    next_steps: list[str]
    generated_at: datetime


class AIRecommendationEngine:
    """
    Uses Azure OpenAI for intelligent recommendations.
    
    Provides:
    - Cap recommendations with business rationale
    - Human-readable decision explanations
    - Market trend analysis
    - Alternative suggestions when requests are blocked
    
    Falls back to rule-based recommendations if AI unavailable.
    
    Attributes:
        db: SQLAlchemy database session.
        client: Azure OpenAI client (if configured).
        deployment: Azure OpenAI deployment name.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the AI Recommendation Engine.
        
        Args:
            db: SQLAlchemy database session.
        """
        self.db = db
        self.settings = get_settings()
        self.client = None
        self.deployment = self.settings.AZURE_OPENAI_DEPLOYMENT
        
        # Initialize Azure OpenAI client if configured
        if self.settings.AZURE_OPENAI_API_KEY:
            try:
                from openai import AzureOpenAI
                self.client = AzureOpenAI(
                    api_key=self.settings.AZURE_OPENAI_API_KEY,
                    api_version=self.settings.AZURE_OPENAI_API_VERSION,
                    azure_endpoint=self.settings.AZURE_OPENAI_ENDPOINT,
                )
            except Exception as e:
                print(f"Warning: Could not initialize Azure OpenAI: {e}")
                self.client = None
        
        # Initialize other engines for data gathering
        self.capacity_engine = CapacityEngine(db)
        self.dominance_engine = DominanceAlertEngine(db)
    
    def generate_cap_recommendation(
        self,
        nationality_id: int
    ) -> CapRecommendation:
        """
        Generate AI-powered cap recommendation for a nationality.
        
        Args:
            nationality_id: ID of the nationality.
            
        Returns:
            CapRecommendation: Detailed recommendation with rationale.
        """
        # Gather data
        nationality = self.db.query(Nationality).filter(
            Nationality.id == nationality_id
        ).first()
        
        if not nationality:
            raise ValueError(f"Nationality {nationality_id} not found")
        
        # Get capacity data
        try:
            headroom = self.capacity_engine.calculate_effective_headroom(
                nationality_id, include_outflow=False
            )
            current_stock = headroom.stock
            current_cap = headroom.cap
        except ValueError:
            current_stock = 0
            current_cap = None
        
        # Get dominance alerts
        alerts = self.dominance_engine.get_all_alerts_for_nationality(nationality_id)
        
        # Calculate recommendations based on data
        if current_cap:
            # Growth-based recommendations
            conservative = int(current_cap * 1.05)  # 5% growth
            moderate = int(current_cap * 1.10)      # 10% growth
            flexible = int(current_cap * 1.20)      # 20% growth
        else:
            # New cap - based on current stock
            conservative = int(current_stock * 1.10)
            moderate = int(current_stock * 1.15)
            flexible = int(current_stock * 1.25)
        
        # Determine recommendation level based on factors
        has_critical_alerts = any(a.alert_level.value == "CRITICAL" for a in alerts)
        has_high_alerts = any(a.alert_level.value == "HIGH" for a in alerts)
        
        if has_critical_alerts:
            recommended = conservative
            level = "conservative"
        elif has_high_alerts:
            recommended = moderate
            level = "moderate"
        else:
            recommended = moderate  # Default to moderate
            level = "moderate"
        
        # Generate rationale
        if self.client:
            rationale = self._generate_ai_rationale(
                nationality.code, current_stock, current_cap,
                conservative, moderate, flexible, level, alerts
            )
        else:
            rationale = self._generate_rule_based_rationale(
                nationality.code, current_stock, current_cap,
                conservative, moderate, flexible, level, alerts
            )
        
        # Key factors
        key_factors = [
            f"Current stock: {current_stock:,} workers",
            f"Current cap: {current_cap:,}" if current_cap else "No current cap",
        ]
        if alerts:
            key_factors.append(f"Active dominance alerts: {len(alerts)}")
        
        # Risks
        risks = []
        if has_critical_alerts:
            risks.append("CRITICAL dominance alerts require immediate attention")
        if current_stock and current_cap and current_stock / current_cap > 0.9:
            risks.append("Near cap limit - may create backlogs")
        
        return CapRecommendation(
            nationality_id=nationality_id,
            nationality_code=nationality.code,
            current_stock=current_stock,
            current_cap=current_cap,
            conservative_cap=conservative,
            moderate_cap=moderate,
            flexible_cap=flexible,
            recommended_cap=recommended,
            recommendation_level=level,
            rationale=rationale,
            key_factors=key_factors,
            risks=risks,
            generated_at=datetime.utcnow(),
        )
    
    def _generate_ai_rationale(
        self,
        nationality_code: str,
        current_stock: int,
        current_cap: Optional[int],
        conservative: int,
        moderate: int,
        flexible: int,
        level: str,
        alerts: list
    ) -> str:
        """Generate rationale using Azure OpenAI."""
        if not self.client:
            return self._generate_rule_based_rationale(
                nationality_code, current_stock, current_cap,
                conservative, moderate, flexible, level, alerts
            )
        
        alerts_text = ""
        if alerts:
            alerts_text = "Active dominance alerts:\n"
            for a in alerts[:3]:  # Top 3 alerts
                alerts_text += f"- {a.profession_name}: {a.share_pct:.1%} share ({a.alert_level.value})\n"
        
        prompt = f"""You are an expert labor market analyst for Qatar's Ministry of Labour.

Generate a brief (2-3 sentences) recommendation rationale for setting the annual cap for {nationality_code} workers.

Current data:
- Current stock: {current_stock:,} workers
- Current cap: {current_cap:,} if current_cap else 'Not set'
- Recommended level: {level}
- Conservative option: {conservative:,}
- Moderate option: {moderate:,}
- Flexible option: {flexible:,}
{alerts_text}

Provide a professional, data-driven rationale. Be specific about why the {level} option is recommended."""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a labor market policy advisor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"AI generation failed: {e}")
            return self._generate_rule_based_rationale(
                nationality_code, current_stock, current_cap,
                conservative, moderate, flexible, level, alerts
            )
    
    def _generate_rule_based_rationale(
        self,
        nationality_code: str,
        current_stock: int,
        current_cap: Optional[int],
        conservative: int,
        moderate: int,
        flexible: int,
        level: str,
        alerts: list
    ) -> str:
        """Generate rationale using rules when AI unavailable."""
        if level == "conservative":
            return (
                f"A conservative cap of {conservative:,} is recommended for {nationality_code} "
                f"due to active dominance alerts. This limits growth to 5% while maintaining "
                f"workforce diversification goals. Current stock is {current_stock:,}."
            )
        elif level == "moderate":
            return (
                f"A moderate cap of {moderate:,} is recommended for {nationality_code}, "
                f"allowing 10% growth from current levels. This balances demand accommodation "
                f"with concentration risk management. Current stock is {current_stock:,}."
            )
        else:
            return (
                f"A flexible cap of {flexible:,} is recommended for {nationality_code}, "
                f"enabling 20% growth to accommodate demand surge. Monitor dominance "
                f"indicators closely. Current stock is {current_stock:,}."
            )
    
    def explain_decision(
        self,
        decision_log: DecisionLog
    ) -> DecisionExplanation:
        """
        Generate human-readable explanation of a decision.
        
        Args:
            decision_log: DecisionLog to explain.
            
        Returns:
            DecisionExplanation: Detailed explanation.
        """
        request = self.db.query(QuotaRequest).filter(
            QuotaRequest.id == decision_log.request_id
        ).first()
        
        decision = decision_log.decision.value
        rule_chain = decision_log.get_rule_chain()
        
        # Build summary
        summary = f"Request {decision}: {request.approved_count} of {request.requested_count} workers approved."
        
        # Build detailed explanation
        if self.client:
            detailed = self._generate_ai_explanation(decision_log, request, rule_chain)
        else:
            detailed = self._generate_rule_based_explanation(decision_log, request, rule_chain)
        
        # Extract factors from rule chain
        factors = []
        for rule in rule_chain:
            factors.append(f"{rule.get('rule', 'Unknown')}: {rule.get('result', 'N/A')}")
        
        # Next steps
        next_steps = []
        if decision == "QUEUED":
            next_steps.append("Request has been added to the auto-queue")
            next_steps.append("Will be processed automatically when capacity opens")
            next_steps.append("Confirmation required after 30 days")
        elif decision == "BLOCKED":
            next_steps.append("Consider alternative nationalities")
            next_steps.append("Request override through appeals process if justified")
        elif decision == "APPROVED":
            next_steps.append("Proceed with visa processing")
        
        return DecisionExplanation(
            request_id=decision_log.request_id,
            decision=decision,
            summary=summary,
            detailed_explanation=detailed,
            factors_considered=factors,
            next_steps=next_steps,
            generated_at=datetime.utcnow(),
        )
    
    def _generate_ai_explanation(
        self,
        decision_log: DecisionLog,
        request: QuotaRequest,
        rule_chain: list
    ) -> str:
        """Generate explanation using Azure OpenAI."""
        if not self.client:
            return self._generate_rule_based_explanation(decision_log, request, rule_chain)
        
        rules_text = "\n".join([
            f"- {r.get('rule')}: {r.get('result')}"
            for r in rule_chain
        ])
        
        prompt = f"""Explain this quota request decision in simple terms:

Decision: {decision_log.decision.value}
Requested workers: {request.requested_count}
Approved workers: {request.approved_count}

Rules evaluated:
{rules_text}

Provide a 2-3 sentence explanation that a business owner would understand."""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You explain government decisions clearly."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return self._generate_rule_based_explanation(decision_log, request, rule_chain)
    
    def _generate_rule_based_explanation(
        self,
        decision_log: DecisionLog,
        request: QuotaRequest,
        rule_chain: list
    ) -> str:
        """Generate explanation using rules when AI unavailable."""
        decision = decision_log.decision.value
        
        if decision == "APPROVED":
            return (
                f"Your request for {request.requested_count} workers has been approved. "
                f"The profession is in an open tier with sufficient capacity, "
                f"and no concentration concerns were identified."
            )
        elif decision == "PARTIAL":
            return (
                f"Your request has been partially approved: {request.approved_count} of "
                f"{request.requested_count} workers. This is due to limited capacity "
                f"in the current tier. Consider submitting another request later."
            )
        elif decision == "QUEUED":
            return (
                f"Your request for {request.requested_count} workers has been queued. "
                f"The tier is currently at capacity. Your request will be automatically "
                f"processed when capacity becomes available."
            )
        elif decision == "BLOCKED":
            return (
                f"Your request has been blocked due to high concentration of this "
                f"nationality in the requested profession. Diversification policies "
                f"require hiring from other nationalities."
            )
        else:
            return f"Your request has been {decision.lower()}. Please contact support for details."
    
    def suggest_alternatives(
        self,
        request: QuotaRequest
    ) -> list[str]:
        """
        Suggest alternatives when a request is blocked or queued.
        
        Args:
            request: The blocked/queued request.
            
        Returns:
            List of alternative suggestions.
        """
        alternatives = []
        
        # Check other nationalities for the same profession
        dominance = self.dominance_engine.check_dominance(
            request.nationality_id,
            request.profession_id
        )
        
        if dominance.is_blocking or dominance.is_partial_only:
            alternatives.append(
                f"Consider workers from nationalities with lower concentration "
                f"in {dominance.profession_name}"
            )
        
        # Check queue status
        alternatives.append(
            "Join the auto-queue for processing when capacity opens"
        )
        
        # Timing suggestion
        alternatives.append(
            "Monitor the dashboard for projected capacity openings"
        )
        
        return alternatives
    
    def analyze_market_trends(
        self,
        nationality_id: int
    ) -> str:
        """
        Analyze market trends for a nationality.
        
        Args:
            nationality_id: Nationality to analyze.
            
        Returns:
            str: Market trend analysis.
        """
        nationality = self.db.query(Nationality).filter(
            Nationality.id == nationality_id
        ).first()
        
        if not nationality:
            return "Nationality not found."
        
        # Get capacity data
        try:
            headroom = self.capacity_engine.calculate_effective_headroom(nationality_id)
        except ValueError:
            return f"No cap data available for {nationality.code}."
        
        # Get alerts
        alerts = self.dominance_engine.get_all_alerts_for_nationality(nationality_id)
        
        if self.client:
            return self._generate_ai_trend_analysis(nationality, headroom, alerts)
        else:
            return self._generate_rule_based_trend_analysis(nationality, headroom, alerts)
    
    def _generate_ai_trend_analysis(self, nationality, headroom, alerts) -> str:
        """Generate trend analysis using Azure OpenAI."""
        if not self.client:
            return self._generate_rule_based_trend_analysis(nationality, headroom, alerts)
        
        alerts_text = ""
        if alerts:
            alerts_text = "Dominance concerns:\n"
            for a in alerts[:3]:
                alerts_text += f"- {a.profession_name}: {a.share_pct:.1%} ({a.alert_level.value})\n"
        
        prompt = f"""Analyze market trends for {nationality.code} workers in Qatar:

Current metrics:
- Stock: {headroom.stock:,} workers
- Cap: {headroom.cap:,}
- Utilization: {headroom.utilization_pct:.1%}
- Headroom: {headroom.effective_headroom:,}
{alerts_text}

Provide a brief (3-4 sentences) analysis of trends and recommendations."""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a labor market analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return self._generate_rule_based_trend_analysis(nationality, headroom, alerts)
    
    def _generate_rule_based_trend_analysis(self, nationality, headroom, alerts) -> str:
        """Generate trend analysis using rules when AI unavailable."""
        analysis = f"{nationality.code} workforce analysis:\n\n"
        analysis += f"Current stock: {headroom.stock:,} ({headroom.utilization_pct:.1%} of cap)\n"
        analysis += f"Available headroom: {headroom.effective_headroom:,} workers\n\n"
        
        if headroom.utilization_pct > 0.9:
            analysis += "WARNING: Near capacity limit. New requests may be queued.\n"
        elif headroom.utilization_pct > 0.7:
            analysis += "Moderate utilization. Consider demand trends before cap changes.\n"
        else:
            analysis += "Healthy headroom available for growth.\n"
        
        if alerts:
            analysis += f"\n{len(alerts)} dominance alert(s) active. "
            analysis += "Diversification recommended in affected professions."
        
        return analysis
