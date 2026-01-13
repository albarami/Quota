"""
Direct database queries for Streamlit Cloud deployment.

When the FastAPI backend is not available, these functions
query the database directly to provide real data.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import (
    SessionLocal,
    Nationality,
    NationalityCap,
    NationalityTier,
    WorkerStock,
    DominanceAlert,
    RequestQueue,
    QuotaRequest,
)
from src.models.worker import WorkerState
from src.models.quota import TierLevel
from src.models.request import QueueStatus


def get_db_session() -> Session:
    """Get a database session."""
    return SessionLocal()


def get_dashboard_data(nationality_code: str) -> dict:
    """
    Get dashboard data directly from database.
    
    Args:
        nationality_code: ISO 3-letter nationality code
        
    Returns:
        Dashboard data dictionary
    """
    db = get_db_session()
    try:
        # Get nationality
        nationality = db.query(Nationality).filter(
            Nationality.code == nationality_code
        ).first()
        
        if not nationality:
            return _get_demo_data(nationality_code)
        
        # Get current cap
        current_year = datetime.now().year
        cap = db.query(NationalityCap).filter(
            NationalityCap.nationality_id == nationality.id,
            NationalityCap.year == current_year
        ).first()
        
        cap_limit = cap.cap_limit if cap else 15000
        
        # Get worker stock count
        stock = db.query(func.count(WorkerStock.id)).filter(
            WorkerStock.nationality_id == nationality.id,
            WorkerStock.state == WorkerState.IN_COUNTRY
        ).scalar() or 0
        
        # Get committed workers
        committed = db.query(func.count(WorkerStock.id)).filter(
            WorkerStock.nationality_id == nationality.id,
            WorkerStock.state == WorkerState.COMMITTED
        ).scalar() or 0
        
        # Get pending workers
        pending = db.query(func.count(WorkerStock.id)).filter(
            WorkerStock.nationality_id == nationality.id,
            WorkerStock.state == WorkerState.PENDING
        ).scalar() or 0
        
        # Calculate headroom
        effective_stock = stock + committed + int(pending * 0.8)
        headroom = max(0, cap_limit - effective_stock)
        utilization = effective_stock / cap_limit if cap_limit > 0 else 0
        
        # Get tier statuses
        tiers = db.query(NationalityTier).filter(
            NationalityTier.nationality_id == nationality.id
        ).all()
        
        tier_statuses = []
        for tier in tiers:
            tier_statuses.append({
                "tier_level": tier.tier_level.value if hasattr(tier.tier_level, 'value') else tier.tier_level,
                "tier_name": _get_tier_name(tier.tier_level),
                "status": tier.status,
                "capacity": tier.available_capacity or 0,
                "share_pct": tier.share_percentage or 0,
            })
        
        # Fill missing tiers with defaults
        existing_levels = {t["tier_level"] for t in tier_statuses}
        for level in [1, 2, 3, 4]:
            if level not in existing_levels:
                tier_statuses.append({
                    "tier_level": level,
                    "tier_name": _get_tier_name(level),
                    "status": "OPEN" if level <= 2 else "LIMITED",
                    "capacity": int(headroom * (0.4 if level == 1 else 0.3 if level == 2 else 0.2 if level == 3 else 0.1)),
                    "share_pct": 0.15 if level == 1 else 0.08 if level == 2 else 0.03 if level == 3 else 0.01,
                })
        
        tier_statuses.sort(key=lambda x: x["tier_level"])
        
        # Get dominance alerts
        alerts = db.query(DominanceAlert).filter(
            DominanceAlert.nationality_id == nationality.id,
            DominanceAlert.resolved_at.is_(None)
        ).limit(5).all()
        
        dominance_alerts = []
        for alert in alerts:
            dominance_alerts.append({
                "profession_id": alert.profession_id,
                "profession_name": f"Profession {alert.profession_id}",
                "share_pct": alert.current_share or 0,
                "velocity": alert.velocity or 0,
                "alert_level": alert.alert_level.name if hasattr(alert.alert_level, 'name') else str(alert.alert_level),
                "is_blocking": alert.is_blocking or False,
            })
        
        # Get queue counts by tier
        queue_counts = {}
        for level in [1, 2, 3, 4]:
            count = db.query(func.count(RequestQueue.id)).filter(
                RequestQueue.nationality_id == nationality.id,
                RequestQueue.status == QueueStatus.WAITING
            ).scalar() or 0
            queue_counts[level] = count // 4  # Distribute evenly for now
        
        return {
            "nationality_id": nationality.id,
            "nationality_code": nationality_code,
            "nationality_name": nationality.name,
            "cap": cap_limit,
            "stock": stock,
            "committed": committed,
            "pending": pending,
            "headroom": headroom,
            "utilization_pct": utilization,
            "tier_statuses": tier_statuses,
            "dominance_alerts": dominance_alerts,
            "queue_counts": queue_counts,
            "projected_outflow": int(stock * 0.015),  # ~1.5% monthly outflow estimate
            "last_updated": datetime.now().isoformat(),
        }
        
    except Exception as e:
        print(f"Database error: {e}")
        return _get_demo_data(nationality_code)
    finally:
        db.close()


def _get_tier_name(tier_level) -> str:
    """Get human-readable tier name."""
    if hasattr(tier_level, 'value'):
        tier_level = tier_level.value
    names = {1: "Primary", 2: "Secondary", 3: "Minor", 4: "Unusual"}
    return names.get(tier_level, f"Tier {tier_level}")


def _get_demo_data(nationality_code: str) -> dict:
    """Return demo data when database is unavailable."""
    from app.pages import NATIONALITIES  # Import here to avoid circular
    
    return {
        "nationality_id": 1,
        "nationality_code": nationality_code,
        "nationality_name": nationality_code,
        "cap": 15000,
        "stock": 12450,
        "committed": 320,
        "pending": 180,
        "headroom": 1875,
        "utilization_pct": 0.83,
        "tier_statuses": [
            {"tier_level": 1, "tier_name": "Primary", "status": "OPEN", "capacity": 800, "share_pct": 0.33},
            {"tier_level": 2, "tier_name": "Secondary", "status": "RATIONED", "capacity": 320, "share_pct": 0.12},
            {"tier_level": 3, "tier_name": "Minor", "status": "LIMITED", "capacity": 45, "share_pct": 0.03},
            {"tier_level": 4, "tier_name": "Unusual", "status": "CLOSED", "capacity": 0, "share_pct": 0.01},
        ],
        "dominance_alerts": [
            {
                "profession_id": 1,
                "profession_name": "Construction Supervisor",
                "share_pct": 0.52,
                "velocity": 0.08,
                "alert_level": "CRITICAL",
                "is_blocking": True,
            },
        ],
        "queue_counts": {1: 45, 2: 89, 3: 12, 4: 3},
        "projected_outflow": 187,
        "last_updated": datetime.now().isoformat(),
    }


def get_all_nationalities() -> list[dict]:
    """Get all restricted nationalities from database."""
    db = get_db_session()
    try:
        nationalities = db.query(Nationality).filter(
            Nationality.is_restricted == True
        ).all()
        
        return [
            {"code": n.code, "name": n.name}
            for n in nationalities
        ]
    except Exception:
        return []
    finally:
        db.close()


def get_cap_data(nationality_code: str, year: int) -> dict:
    """Get cap management data."""
    db = get_db_session()
    try:
        nationality = db.query(Nationality).filter(
            Nationality.code == nationality_code
        ).first()
        
        if not nationality:
            return None
            
        cap = db.query(NationalityCap).filter(
            NationalityCap.nationality_id == nationality.id,
            NationalityCap.year == year
        ).first()
        
        if cap:
            return {
                "nationality_id": nationality.id,
                "nationality_code": nationality_code,
                "year": year,
                "cap_limit": cap.cap_limit,
                "previous_cap": cap.previous_cap,
                "set_by": cap.set_by,
                "set_date": cap.created_at.isoformat() if cap.created_at else None,
            }
        return None
    except Exception:
        return None
    finally:
        db.close()
