"""
Dashboard API routes.

Provides real-time monitoring data for nationalities using v4 methodology.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add project root for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.schemas.models import (
    AlertLevelEnum,
    TierStatusEnum,
)

router = APIRouter()


# ============================================
# v4 Response Schemas
# ============================================

class TierStatusV4(BaseModel):
    """Tier status with v4 metrics."""
    tier_level: int
    tier_name: str
    status: TierStatusEnum
    capacity: int
    share_pct: Optional[float] = None
    profession_count: int = 0
    worker_count: int = 0


class DominanceAlertV4(BaseModel):
    """Dominance alert information."""
    profession_code: str
    profession_name: str
    nationality_workers: int
    total_in_profession: int
    share_pct: float
    alert_level: AlertLevelEnum
    is_blocking: bool


class DashboardV4Response(BaseModel):
    """Dashboard data with v4 methodology."""
    # Identity
    nationality_code: str
    nationality_name: str
    country_type: str
    
    # Stock & Cap
    current_stock: int
    recommended_cap: int
    headroom: int
    utilization_pct: float
    
    # v4 Flow Data
    avg_annual_joiners: int
    avg_annual_outflow: int
    joined_2024: int
    joined_2025: int
    left_2024: int
    left_2025: int
    
    # v4 Growth
    growth_direction: str
    growth_rate: float
    net_growth: int
    
    # v4 Demand
    demand_basis: str
    demand_value: int
    buffer_pct: float
    buffer_value: int
    desired_cap: int
    
    # QVC Constraint (optional)
    qvc_annual_capacity: Optional[int] = None
    net_qvc_capacity: Optional[int] = None
    max_achievable_cap: Optional[int] = None
    is_qvc_constrained: bool = False
    qvc_utilization_pct: Optional[float] = None
    
    # Monthly allocation (outflow-based)
    monthly_allocation: Optional[int] = None
    
    # Tiers and Alerts
    tier_statuses: list[TierStatusV4]
    dominance_alerts: list[DominanceAlertV4]
    alert_count: int
    has_critical: bool
    
    # Queue
    queue_counts: dict
    projected_outflow: int
    
    # Metadata
    last_updated: datetime
    data_source: str
    formula_version: str


class DashboardOverviewV4(BaseModel):
    """Overview of all nationalities with v4 metrics."""
    nationalities: list[DashboardV4Response]
    total_restricted: int
    total_workers: int
    total_recommended_cap: int
    total_headroom: int


# ============================================
# API Routes
# ============================================

@router.get("/{nationality_code}", response_model=DashboardV4Response)
async def get_nationality_dashboard(nationality_code: str):
    """
    Get live dashboard data for a specific nationality using v4 methodology.
    
    Returns all v4 metrics including:
    - Cap, stock, headroom, utilization
    - Growth direction and demand basis
    - QVC constraint status (for QVC countries)
    - Tier statuses and dominance alerts
    """
    from src.engines.quota_engine import get_all_metrics, get_all_nationalities
    
    # Validate nationality code
    valid_codes = get_all_nationalities()
    code = nationality_code.upper()
    
    if code not in valid_codes:
        raise HTTPException(
            status_code=404,
            detail=f"Nationality {nationality_code} not found. Valid codes: {', '.join(valid_codes)}"
        )
    
    # Get metrics from quota engine
    try:
        metrics = get_all_metrics(code)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating metrics: {str(e)}"
        )
    
    # Build tier statuses
    tier_names = {1: "Primary", 2: "Secondary", 3: "Minor", 4: "Unusual"}
    tier_statuses = []
    
    headroom = metrics['headroom']
    utilization = metrics['utilization_pct'] / 100
    
    for tier_level in [1, 2, 3, 4]:
        tier_data = metrics['tier_summary'].get(str(tier_level), {})
        tier_share = tier_data.get('share', 0)
        
        # Calculate tier capacity based on headroom allocation
        allocation_pct = {1: 0.40, 2: 0.30, 3: 0.20, 4: 0.10}
        tier_cap = int(headroom * allocation_pct[tier_level])
        
        # Determine status
        if metrics['country_type'] == 'OUTFLOW_BASED':
            status = TierStatusEnum.CLOSED
        elif utilization >= 0.95:
            status = TierStatusEnum.CLOSED
        elif utilization >= 0.90:
            status = TierStatusEnum.LIMITED if tier_level <= 2 else TierStatusEnum.CLOSED
        elif utilization >= 0.80:
            if tier_level == 1:
                status = TierStatusEnum.RATIONED
            elif tier_level == 2:
                status = TierStatusEnum.LIMITED
            else:
                status = TierStatusEnum.CLOSED
        else:
            if tier_level <= 2:
                status = TierStatusEnum.OPEN
            elif tier_level == 3:
                status = TierStatusEnum.RATIONED
            else:
                status = TierStatusEnum.LIMITED
        
        tier_statuses.append(TierStatusV4(
            tier_level=tier_level,
            tier_name=tier_names[tier_level],
            status=status,
            capacity=tier_cap,
            share_pct=tier_share,
            profession_count=tier_data.get('profession_count', 0),
            worker_count=tier_data.get('worker_count', 0),
        ))
    
    # Build dominance alerts
    dominance_alerts = []
    for alert in metrics.get('dominance_alerts', []):
        dominance_alerts.append(DominanceAlertV4(
            profession_code=alert.get('profession_code', ''),
            profession_name=alert.get('profession_name', ''),
            nationality_workers=alert.get('nationality_workers', 0),
            total_in_profession=alert.get('total_in_profession', 0),
            share_pct=alert.get('share_pct', 0),
            alert_level=AlertLevelEnum(alert.get('alert_level', 'OK')),
            is_blocking=alert.get('is_blocking', False),
        ))
    
    # Queue counts (estimated)
    queue_counts = {
        1: max(0, int(headroom * 0.05)),
        2: max(0, int(headroom * 0.08)),
        3: max(0, int(headroom * 0.02)),
        4: max(0, int(headroom * 0.01)),
    }
    
    # Projected outflow
    projected_outflow = int(metrics['current_stock'] * 0.015 * 3)
    
    return DashboardV4Response(
        nationality_code=code,
        nationality_name=metrics['nationality_name'],
        country_type=metrics['country_type'],
        current_stock=metrics['current_stock'],
        recommended_cap=metrics['recommended_cap'],
        headroom=metrics['headroom'],
        utilization_pct=metrics['utilization_pct'],
        avg_annual_joiners=metrics['avg_annual_joiners'],
        avg_annual_outflow=metrics['avg_annual_outflow'],
        joined_2024=metrics['joined_2024'],
        joined_2025=metrics['joined_2025'],
        left_2024=metrics['left_2024'],
        left_2025=metrics['left_2025'],
        growth_direction=metrics['growth_direction'],
        growth_rate=metrics['growth_rate'],
        net_growth=metrics['net_growth'],
        demand_basis=metrics['demand_basis'],
        demand_value=metrics['demand_value'],
        buffer_pct=metrics['buffer_pct'],
        buffer_value=metrics['buffer_value'],
        desired_cap=metrics['desired_cap'],
        qvc_annual_capacity=metrics.get('qvc_annual_capacity'),
        net_qvc_capacity=metrics.get('net_qvc_capacity'),
        max_achievable_cap=metrics.get('max_achievable_cap'),
        is_qvc_constrained=metrics.get('is_qvc_constrained', False),
        qvc_utilization_pct=metrics.get('qvc_utilization_pct'),
        monthly_allocation=metrics.get('monthly_allocation'),
        tier_statuses=tier_statuses,
        dominance_alerts=dominance_alerts,
        alert_count=metrics['alert_count'],
        has_critical=metrics['has_critical'],
        queue_counts=queue_counts,
        projected_outflow=projected_outflow,
        last_updated=datetime.utcnow(),
        data_source='quota_engine_v4',
        formula_version='4.0',
    )


@router.get("/", response_model=DashboardOverviewV4)
async def get_dashboard_overview():
    """
    Get overview of all restricted nationalities using v4 methodology.
    
    Returns summary data for all 12 restricted nationalities.
    """
    from src.engines.quota_engine import get_all_metrics, get_all_nationalities
    
    all_codes = get_all_nationalities()
    nationalities = []
    total_workers = 0
    total_cap = 0
    total_headroom = 0
    
    for code in all_codes:
        try:
            # Get data for each nationality
            response = await get_nationality_dashboard(code)
            nationalities.append(response)
            total_workers += response.current_stock
            total_cap += response.recommended_cap
            total_headroom += response.headroom
        except Exception:
            # Skip nationalities with errors
            continue
    
    return DashboardOverviewV4(
        nationalities=nationalities,
        total_restricted=len(all_codes),
        total_workers=total_workers,
        total_recommended_cap=total_cap,
        total_headroom=total_headroom,
    )


@router.get("/summary/{nationality_code}")
async def get_nationality_summary(nationality_code: str):
    """
    Get a simple summary for a nationality.
    
    Lightweight endpoint returning just key v4 metrics.
    """
    from src.engines.quota_engine import get_all_metrics, get_all_nationalities
    
    valid_codes = get_all_nationalities()
    code = nationality_code.upper()
    
    if code not in valid_codes:
        raise HTTPException(status_code=404, detail=f"Nationality {code} not found")
    
    metrics = get_all_metrics(code)
    
    return {
        'nationality_code': code,
        'nationality_name': metrics['nationality_name'],
        'country_type': metrics['country_type'],
        'stock': metrics['current_stock'],
        'recommended_cap': metrics['recommended_cap'],
        'headroom': metrics['headroom'],
        'utilization_pct': metrics['utilization_pct'],
        'growth_direction': metrics['growth_direction'],
        'growth_rate': metrics['growth_rate'],
        'demand_basis': metrics['demand_basis'],
        'is_qvc_constrained': metrics.get('is_qvc_constrained', False),
    }
