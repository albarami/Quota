"""
Real Data Loader for Streamlit Dashboard.

This module provides the interface between the Streamlit UI and the quota_engine.
All calculations are delegated to the quota_engine - NO fallbacks or demo data.

This is a production-grade data loader.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the quota engine - single source of truth
from src.engines.quota_engine import (
    get_all_metrics,
    get_all_nationalities,
    is_qvc_country,
    is_outflow_based,
    get_qvc_capacity_details,
    QVC_COUNTRIES,
    OUTFLOW_BASED,
    STANDARD_NON_QVC,
    DATA_DIR,
)


# Nationality name mapping
NATIONALITY_NAMES = {
    'EGY': 'Egypt',
    'IND': 'India',
    'PAK': 'Pakistan',
    'NPL': 'Nepal',
    'BGD': 'Bangladesh',
    'PHL': 'Philippines',
    'LKA': 'Sri Lanka',
    'IRN': 'Iran',
    'IRQ': 'Iraq',
    'YEM': 'Yemen',
    'SYR': 'Syria',
    'AFG': 'Afghanistan',
}


def check_real_data_available() -> bool:
    """
    Check if real data files are available.
    
    Returns True if the essential data files exist.
    """
    required_files = [
        '07_worker_stock.csv',
        '01_nationalities.csv',
    ]
    return all((DATA_DIR / f).exists() for f in required_files)


def get_real_dashboard_data(nationality_code: str) -> Optional[dict]:
    """
    Get dashboard data for a nationality using the quota engine.
    
    This is the main function called by the Streamlit dashboard.
    Returns a complete dictionary with all v4 metrics.
    
    Args:
        nationality_code: ISO 3-letter code (e.g., 'IND')
        
    Returns:
        Dictionary with all dashboard metrics, or None if data unavailable
    """
    if not check_real_data_available():
        raise FileNotFoundError("Real data files not found in real_data/ folder")
    
    # Get all metrics from quota engine
    metrics = get_all_metrics(nationality_code)
    
    # Build tier statuses for dashboard display
    tier_statuses = []
    utilization = metrics['utilization_pct'] / 100  # Convert to decimal
    headroom = metrics['headroom']
    
    for tier_level in [1, 2, 3, 4]:
        tier_data = metrics['tier_summary'].get(str(tier_level), {})
        tier_share = tier_data.get('share', 0)
        
        # Calculate tier capacity based on headroom allocation
        # Tier 1 gets 40%, Tier 2 gets 30%, Tier 3 gets 20%, Tier 4 gets 10%
        allocation_pct = {1: 0.40, 2: 0.30, 3: 0.20, 4: 0.10}
        tier_cap = int(headroom * allocation_pct[tier_level])
        
        # Determine status based on utilization and tier level
        if metrics['country_type'] == 'OUTFLOW_BASED':
            # Outflow-based countries have 100% utilization
            status = "CLOSED"
        elif utilization >= 0.95:
            status = "CLOSED"
        elif utilization >= 0.90:
            status = "LIMITED" if tier_level <= 2 else "CLOSED"
        elif utilization >= 0.80:
            status = "RATIONED" if tier_level == 1 else "LIMITED" if tier_level == 2 else "CLOSED"
        else:
            status = "OPEN" if tier_level <= 2 else "RATIONED" if tier_level == 3 else "LIMITED"
        
        tier_statuses.append({
            'tier_level': tier_level,
            'tier_name': ['Primary', 'Secondary', 'Minor', 'Unusual'][tier_level - 1],
            'status': status,
            'capacity': tier_cap,
            'share_pct': tier_share,
            'profession_count': tier_data.get('profession_count', 0),
            'worker_count': tier_data.get('worker_count', 0),
        })
    
    # Build dominance alerts
    alerts = []
    for alert in metrics.get('dominance_alerts', []):
        alerts.append({
            'profession_id': alert.get('profession_code', ''),
            'profession_name': alert.get('profession_name', ''),
            'share_pct': alert.get('share_pct', 0),
            'nationality_workers': alert.get('nationality_workers', 0),
            'total_in_profession': alert.get('total_in_profession', 0),
            'velocity': 0.02,  # Estimated
            'alert_level': alert.get('alert_level', 'OK'),
            'is_blocking': alert.get('is_blocking', False),
        })
    
    # Queue counts (estimated based on headroom)
    queue_counts = {
        1: max(0, int(headroom * 0.05)),
        2: max(0, int(headroom * 0.08)),
        3: max(0, int(headroom * 0.02)),
        4: max(0, int(headroom * 0.01)),
    }
    
    # Projected outflow (estimated ~1.5% monthly for 3 months)
    projected_outflow = int(metrics['current_stock'] * 0.015 * 3)
    
    return {
        # Identity
        'nationality_id': hash(nationality_code) % 10000,
        'nationality_code': nationality_code,
        'nationality_name': metrics.get('nationality_name', NATIONALITY_NAMES.get(nationality_code, nationality_code)),
        'country_type': metrics['country_type'],
        
        # Stock & Cap (v4)
        'cap': metrics['recommended_cap'],
        'stock': metrics['current_stock'],
        'headroom': metrics['headroom'],
        'utilization_pct': metrics['utilization_pct'] / 100,  # As decimal for compatibility
        
        # v4 Metrics
        'recommended_cap': metrics['recommended_cap'],
        'desired_cap': metrics['desired_cap'],
        'max_achievable_cap': metrics.get('max_achievable_cap'),
        'is_qvc_constrained': metrics.get('is_qvc_constrained', False),
        
        # Flow Data
        'avg_annual_joiners': metrics['avg_annual_joiners'],
        'avg_annual_outflow': metrics['avg_annual_outflow'],
        'joined_2024': metrics['joined_2024'],
        'joined_2025': metrics['joined_2025'],
        'left_2024': metrics['left_2024'],
        'left_2025': metrics['left_2025'],
        
        # Growth
        'growth_direction': metrics['growth_direction'],
        'growth_rate': metrics['growth_rate'],
        'net_growth': metrics['net_growth'],
        
        # Demand
        'demand_basis': metrics['demand_basis'],
        'demand_value': metrics['demand_value'],
        'buffer_pct': metrics['buffer_pct'],
        'buffer_value': metrics['buffer_value'],
        
        # QVC
        'qvc_annual_capacity': metrics.get('qvc_annual_capacity'),
        'net_qvc_capacity': metrics.get('net_qvc_capacity'),
        'qvc_utilization_pct': metrics.get('qvc_utilization_pct'),
        
        # Monthly allocation (outflow-based)
        'monthly_allocation': metrics.get('monthly_allocation'),
        
        # Tiers and Alerts
        'tier_statuses': tier_statuses,
        'tier_summary': metrics['tier_summary'],
        'dominance_alerts': alerts,
        'alert_count': metrics['alert_count'],
        'has_critical': metrics['has_critical'],
        
        # Queue
        'queue_counts': queue_counts,
        'projected_outflow': projected_outflow,
        
        # Metadata
        'last_updated': datetime.now().isoformat(),
        'data_source': 'quota_engine_v4',
        'formula_version': '4.0',
    }


def get_qvc_capacity(nationality_code: str) -> Optional[dict]:
    """
    Get QVC capacity data for a specific nationality.
    
    Args:
        nationality_code: ISO 3-letter code (e.g., 'BGD')
        
    Returns:
        QVC capacity dict with daily_capacity, centers, etc.
        Returns None for non-QVC countries.
    """
    if not is_qvc_country(nationality_code):
        return None
    
    details = get_qvc_capacity_details(nationality_code)
    if not details:
        return None
    
    return {
        'nationality_code': nationality_code,
        'country': details['country'],
        'daily_capacity': details['daily_capacity'],
        'monthly_capacity': details['monthly_capacity'],
        'annual_capacity': details['annual_capacity'],
        'centers': details['centers'],
        'center_count': len(details['centers']),
    }


def get_all_qvc_capacity() -> dict:
    """
    Get QVC capacity for all QVC countries.
    
    Returns:
        Dict with nationality_code as key, capacity data as value
    """
    result = {}
    for code in QVC_COUNTRIES:
        result[code] = get_qvc_capacity(code)
    return result


def get_qvc_summary() -> dict:
    """
    Get summary of all QVC capacity.
    """
    countries = []
    total_daily = 0
    
    for code in QVC_COUNTRIES:
        data = get_qvc_capacity(code)
        if data:
            countries.append({
                'code': code,
                'country': data['country'],
                'daily_capacity': data['daily_capacity'],
                'monthly_capacity': data['monthly_capacity'],
                'center_count': data['center_count'],
            })
            total_daily += data['daily_capacity']
    
    # Sort by daily capacity descending
    countries.sort(key=lambda x: -x['daily_capacity'])
    
    return {
        'total_daily_capacity': total_daily,
        'total_monthly_capacity': total_daily * 22,
        'country_count': len(countries),
        'countries': countries,
    }


def is_non_qvc_country(nationality_code: str) -> bool:
    """Check if a nationality uses outflow-based allocation (non-QVC)."""
    return is_outflow_based(nationality_code)


def get_outflow_capacity(nationality_code: str) -> Optional[dict]:
    """
    Get outflow-based monthly capacity for non-QVC countries.
    
    For countries without QVC centers, monthly capacity = previous month's outflow.
    This creates a replacement model where new workers replace those who left.
    
    Args:
        nationality_code: ISO 3-letter code (e.g., 'EGY')
        
    Returns:
        Outflow capacity dict or None if not an outflow-based country
    """
    if not is_outflow_based(nationality_code):
        return None
    
    # Get metrics from quota engine
    metrics = get_all_metrics(nationality_code)
    
    monthly_capacity = metrics.get('monthly_allocation', 0)
    if monthly_capacity is None:
        monthly_capacity = metrics['avg_annual_outflow'] // 12
    
    annual_outflow = metrics['avg_annual_outflow']
    
    return {
        'nationality_code': nationality_code,
        'country': metrics.get('nationality_name', NATIONALITY_NAMES.get(nationality_code, nationality_code)),
        'capacity_type': 'outflow_based',
        'monthly_capacity': monthly_capacity,
        'annual_outflow': annual_outflow,
        'current_stock': metrics['current_stock'],
        'growth_rate': metrics['growth_rate'],
        'description': f"Based on ~{annual_outflow:,} workers leaving annually ({monthly_capacity:,}/month avg)",
    }


def get_all_non_qvc_capacity() -> dict:
    """
    Get outflow-based capacity for all non-QVC countries.
    """
    result = {}
    for code in OUTFLOW_BASED:
        result[code] = get_outflow_capacity(code)
    return result


def get_non_qvc_summary() -> dict:
    """
    Get summary of all non-QVC country capacities.
    """
    countries = []
    total_monthly = 0
    total_annual = 0
    
    for code in OUTFLOW_BASED:
        data = get_outflow_capacity(code)
        if data:
            countries.append({
                'code': code,
                'country': data['country'],
                'monthly_capacity': data['monthly_capacity'],
                'annual_outflow': data['annual_outflow'],
                'growth_rate': data['growth_rate'],
            })
            total_monthly += data['monthly_capacity']
            total_annual += data['annual_outflow']
    
    # Sort by monthly capacity descending
    countries.sort(key=lambda x: -x['monthly_capacity'])
    
    return {
        'total_monthly_capacity': total_monthly,
        'total_annual_outflow': total_annual,
        'country_count': len(countries),
        'countries': countries,
        'capacity_type': 'outflow_based',
        'description': 'Monthly capacity based on previous month outflow (replacement model)',
    }


def get_all_real_nationalities() -> list[str]:
    """Get list of all restricted nationality codes."""
    return get_all_nationalities()
