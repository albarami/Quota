#!/usr/bin/env python
"""
Real Data Loader for Streamlit Dashboard.

Loads actual ministry data from CSV files in real_data/ folder.
Uses pre-computed summary for fast loading.
"""

import csv
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Path to real data
REAL_DATA_DIR = project_root / 'real_data'
SUMMARY_FILE = REAL_DATA_DIR / 'summary_by_nationality.json'
QVC_CAPACITY_FILE = REAL_DATA_DIR / 'qvc_capacity.json'

# Cache for summary data
_summary_cache = None
_qvc_cache = None

# Nationality code mapping (ISO 3-letter to numeric)
NATIONALITY_CODES = {
    'EGY': '818',   # Egypt
    'IND': '356',   # India
    'PAK': '586',   # Pakistan
    'NPL': '524',   # Nepal
    'BGD': '050',   # Bangladesh
    'PHL': '608',   # Philippines
    'IRN': '364',   # Iran
    'IRQ': '368',   # Iraq
    'YEM': '886',   # Yemen
    'SYR': '760',   # Syria
    'AFG': '004',   # Afghanistan
    'LKA': '144',   # Sri Lanka
}

# Reverse mapping
NUMERIC_TO_ISO = {v: k for k, v in NATIONALITY_CODES.items()}


def _load_summary() -> Optional[dict]:
    """Load pre-computed summary data (fast)."""
    global _summary_cache
    
    if _summary_cache is not None:
        return _summary_cache
    
    if not SUMMARY_FILE.exists():
        return None
    
    try:
        with open(SUMMARY_FILE, encoding='utf-8') as f:
            _summary_cache = json.load(f)
        return _summary_cache
    except Exception:
        return None


def _load_csv(filename: str) -> list:
    """Load a CSV file from real_data directory."""
    filepath = REAL_DATA_DIR / filename
    if not filepath.exists():
        return []
    
    with open(filepath, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _load_nationalities() -> dict:
    """Load nationality reference data."""
    rows = _load_csv('01_nationalities.csv')
    return {row['code']: row for row in rows}


def _load_professions() -> dict:
    """Load profession reference data."""
    rows = _load_csv('02_professions.csv')
    return {row['code']: row.get('name_en', row.get('name', f'Profession_{row["code"]}')) for row in rows}


def _load_caps() -> dict:
    """Load nationality caps."""
    rows = _load_csv('05_nationality_caps.csv')
    caps = {}
    for row in rows:
        nat_code = row.get('nationality_code', '')
        if nat_code:
            caps[nat_code] = {
                'current_cap': int(row.get('cap_limit', 0) or row.get('current_cap', 0) or 0),
                'previous_cap': int(row.get('previous_cap', 0) or 0),
                'base_cap': int(row.get('base_cap', 0) or 0),
            }
    return caps


def _load_worker_stock() -> list:
    """Load worker stock data (slow - use summary instead)."""
    return _load_csv('07_worker_stock.csv')


def get_real_dashboard_data(nationality_code: str) -> Optional[dict]:
    """
    Get dashboard data from real ministry data files.
    Uses pre-computed summary for fast loading.
    
    Args:
        nationality_code: ISO 3-letter code (e.g., 'EGY')
        
    Returns:
        Dashboard data dictionary with real numbers
    """
    # Try fast path: use pre-computed summary
    summary = _load_summary()
    if summary and nationality_code in summary.get('nationalities', {}):
        return _build_dashboard_from_summary(nationality_code, summary['nationalities'][nationality_code])
    
    # Fallback: compute from raw data (slow)
    return _compute_dashboard_from_raw(nationality_code)


def _build_dashboard_from_summary(nationality_code: str, data: dict) -> dict:
    """Build dashboard response from pre-computed summary (fast)."""
    stock = data['stock']
    cap = data['cap']
    headroom = data['headroom']
    utilization = data['utilization']
    
    # Build tier statuses from summary
    tier_statuses = []
    for tier_level in [1, 2, 3, 4]:
        tier_data = data['tier_summary'].get(str(tier_level), {})
        tier_share = tier_data.get('share', 0)
        tier_cap = int(headroom * (0.40 if tier_level == 1 else 0.30 if tier_level == 2 else 0.20 if tier_level == 3 else 0.10))
        
        # Determine status based on utilization
        if utilization >= 0.95:
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
        })
    
    # Build alerts from summary
    alerts = []
    for alert in data.get('dominance_alerts', []):
        alerts.append({
            'profession_id': alert['profession_code'],
            'profession_name': alert['profession_name'],
            'share_pct': alert['share'],
            'velocity': 0.02,
            'alert_level': alert['alert_level'],
            'is_blocking': alert.get('is_blocking', False)
        })
    
    # Queue counts (estimate based on headroom)
    queue_counts = {
        1: max(0, int(headroom * 0.05)),
        2: max(0, int(headroom * 0.08)),
        3: max(0, int(headroom * 0.02)),
        4: max(0, int(headroom * 0.01)),
    }
    
    # Projected outflow (estimate ~1.5% monthly for 3 months)
    projected_outflow = int(stock * 0.015 * 3)
    
    # Growth rates calculated from actual 2024-2025 worker movement data
    # Formula: (Joined_2025 - Left_2025) / Stock_End_2024 × 100
    GROWTH_RATES = {
        'BGD': +0.92,   # Bangladesh: GROWING +3,649 workers
        'PAK': +0.74,   # Pakistan: GROWING +1,443 workers
        'YEM': -1.26,   # Yemen: -167 workers
        'IRQ': -6.38,   # Iraq: -113 workers
        'IRN': -6.79,   # Iran: -487 workers
        'NPL': -9.17,   # Nepal: -34,980 workers
        'AFG': -9.47,   # Afghanistan: -265 workers
        'EGY': -10.79,  # Egypt: -8,661 workers
        'IND': -11.95,  # India: -71,868 workers
        'SYR': -12.37,  # Syria: -3,291 workers
        'PHL': -13.34,  # Philippines: -19,490 workers
        'LKA': -17.39,  # Sri Lanka: -21,317 workers
    }
    growth_rate = GROWTH_RATES.get(nationality_code, 0)
    
    return {
        'nationality_id': int(data['numeric_code']) if data['numeric_code'].isdigit() else 1,
        'nationality_code': nationality_code,
        'nationality_name': data['name'],
        'cap': cap,
        'previous_cap': data.get('previous_cap', 0),
        'stock': stock,
        'in_country': data.get('in_country', stock),
        'out_country': data.get('out_country', 0),
        'committed': data.get('committed', 0),
        'pending': data.get('pending', 0),
        'headroom': headroom,
        'utilization_pct': utilization,
        'tier_statuses': tier_statuses,
        'dominance_alerts': alerts[:5],
        'queue_counts': queue_counts,
        'projected_outflow': projected_outflow,
        'growth_rate': growth_rate,
        'last_updated': datetime.now().isoformat(),
        'data_source': 'summary',
    }


def _compute_dashboard_from_raw(nationality_code: str) -> Optional[dict]:
    """Compute dashboard from raw CSV files (slow fallback)."""
    # Convert to numeric code
    numeric_code = NATIONALITY_CODES.get(nationality_code)
    if not numeric_code:
        return None
    
    # Check if real data exists
    if not REAL_DATA_DIR.exists():
        return None
    
    try:
        # Load reference data
        nationalities = _load_nationalities()
        professions = _load_professions()
        caps = _load_caps()
        
        # Get nationality info
        nat_info = nationalities.get(numeric_code, {})
        nat_name = nat_info.get('name', nationality_code)
        
        # Get cap info
        cap_info = caps.get(numeric_code, {})
        current_cap = cap_info.get('current_cap', 0)
        previous_cap = cap_info.get('previous_cap', 0)
        
        # Load and filter worker stock
        workers = _load_worker_stock()
        
        # Filter by nationality and count by state
        in_country = 0
        out_country = 0
        committed = 0
        pending = 0
        
        profession_counts = defaultdict(int)
        
        for w in workers:
            w_nat = w.get('nationality_code', '') or w.get('nationality', '')
            if w_nat != numeric_code:
                continue
            
            state = w.get('state', '').upper()
            if state in ('ACTIVE', 'IN_COUNTRY', ''):
                in_country += 1
                # Count professions for tier analysis
                prof_code = w.get('profession_code', 'Unknown')
                profession_counts[prof_code] += 1
            elif state == 'OUT_COUNTRY':
                out_country += 1
            elif state == 'COMMITTED':
                committed += 1
            elif state == 'PENDING':
                pending += 1
        
        # Calculate current stock (in-country workers)
        stock = in_country
        
        # Calculate utilization
        headroom = max(0, current_cap - stock - committed - int(pending * 0.8)) if current_cap > 0 else 0
        utilization = stock / current_cap if current_cap > 0 else 0
        
        # Calculate tier distribution
        total_workers = sum(profession_counts.values())
        tier_summary = {1: {'count': 0, 'workers': 0, 'profs': []},
                       2: {'count': 0, 'workers': 0, 'profs': []},
                       3: {'count': 0, 'workers': 0, 'profs': []},
                       4: {'count': 0, 'workers': 0, 'profs': []}}
        
        alerts = []
        
        for prof_code, count in sorted(profession_counts.items(), key=lambda x: -x[1]):
            share = count / total_workers if total_workers > 0 else 0
            
            # Determine tier
            if share >= 0.15:
                tier = 1
            elif share >= 0.05:
                tier = 2
            elif share >= 0.01:
                tier = 3
            else:
                tier = 4
            
            tier_summary[tier]['count'] += 1
            tier_summary[tier]['workers'] += count
            
            if len(tier_summary[tier]['profs']) < 5:
                tier_summary[tier]['profs'].append({
                    'code': prof_code,
                    'name': professions.get(prof_code, f'Code_{prof_code}'),
                    'count': count,
                    'share': share
                })
            
            # Check for dominance alerts
            if share >= 0.30:
                level = "CRITICAL" if share >= 0.50 else "HIGH" if share >= 0.40 else "WATCH"
                alerts.append({
                    'profession_id': prof_code,
                    'profession_name': professions.get(prof_code, f'Code_{prof_code}'),
                    'share_pct': share,
                    'velocity': 0.02,  # Estimate
                    'alert_level': level,
                    'is_blocking': share >= 0.50
                })
        
        # Build tier statuses
        tier_statuses = []
        for tier_level in [1, 2, 3, 4]:
            ts = tier_summary[tier_level]
            tier_share = ts['workers'] / total_workers if total_workers > 0 else 0
            tier_cap = int(headroom * (0.40 if tier_level == 1 else 0.30 if tier_level == 2 else 0.20 if tier_level == 3 else 0.10))
            
            # Determine status based on capacity
            if utilization >= 0.95:
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
            })
        
        # Projected outflow (estimate ~1.5% monthly)
        projected_outflow = int(stock * 0.015 * 3)  # 3 months
        
        # Queue counts (estimate)
        queue_counts = {
            1: max(0, int(headroom * 0.05)),
            2: max(0, int(headroom * 0.08)),
            3: max(0, int(headroom * 0.02)),
            4: max(0, int(headroom * 0.01)),
        }
        
        return {
            'nationality_id': int(numeric_code) if numeric_code.isdigit() else 1,
            'nationality_code': nationality_code,
            'nationality_name': nat_name,
            'cap': current_cap,
            'previous_cap': previous_cap,
            'stock': stock,
            'in_country': in_country,
            'out_country': out_country,
            'committed': committed,
            'pending': pending,
            'headroom': headroom,
            'utilization_pct': utilization,
            'tier_statuses': tier_statuses,
            'dominance_alerts': alerts[:5],  # Limit to 5 alerts
            'queue_counts': queue_counts,
            'projected_outflow': projected_outflow,
            'last_updated': datetime.now().isoformat(),
            'data_source': 'real_data',
        }
        
    except Exception as e:
        print(f"Error loading real data: {e}")
        return None


def check_real_data_available() -> bool:
    """Check if real data files are available (summary OR raw data)."""
    # First check for pre-computed summary (preferred for Streamlit Cloud)
    if SUMMARY_FILE.exists():
        return True
    # Fall back to checking raw CSV files
    required_files = ['07_worker_stock.csv', '01_nationalities.csv']
    return all((REAL_DATA_DIR / f).exists() for f in required_files)


def get_all_real_nationalities() -> list:
    """Get list of nationalities with real data."""
    if not check_real_data_available():
        return []
    
    workers = _load_worker_stock()
    nat_codes = set()
    
    for w in workers:
        nat_code = w.get('nationality_code', '') or w.get('nationality', '')
        if nat_code:
            nat_codes.add(nat_code)
    
    # Map to ISO codes
    result = []
    for numeric in nat_codes:
        iso = NUMERIC_TO_ISO.get(numeric)
        if iso:
            result.append(iso)
    
    return sorted(result)


# =============================================================================
# QVC (Qatar Visa Center) Capacity Functions
# =============================================================================

def _load_qvc_capacity() -> Optional[dict]:
    """Load QVC capacity data from JSON file."""
    global _qvc_cache
    
    if _qvc_cache is not None:
        return _qvc_cache
    
    if not QVC_CAPACITY_FILE.exists():
        return None
    
    try:
        with open(QVC_CAPACITY_FILE, encoding='utf-8') as f:
            _qvc_cache = json.load(f)
        return _qvc_cache
    except Exception:
        return None


def get_qvc_capacity(nationality_code: str) -> Optional[dict]:
    """
    Get QVC capacity data for a specific nationality.
    
    Args:
        nationality_code: ISO 3-letter code (e.g., 'BGD')
        
    Returns:
        QVC capacity dict with daily_capacity, centers, etc.
        Returns None for non-QVC countries (EGY, YEM, SYR, IRQ, AFG, IRN)
    """
    qvc_data = _load_qvc_capacity()
    if not qvc_data:
        return None
    
    centers = qvc_data.get('centers', {})
    if nationality_code not in centers:
        return None  # Not a QVC country
    
    center_data = centers[nationality_code]
    return {
        'nationality_code': nationality_code,
        'country': center_data['country'],
        'daily_capacity': center_data['total_daily_capacity'],
        'monthly_capacity': center_data['total_daily_capacity'] * 22,  # 22 working days
        'centers': center_data['centers'],
        'center_count': len(center_data['centers']),
    }


def get_all_qvc_capacity() -> dict:
    """
    Get QVC capacity for all QVC countries.
    
    Returns:
        Dict with nationality_code as key, capacity data as value
    """
    qvc_data = _load_qvc_capacity()
    if not qvc_data:
        return {}
    
    result = {}
    for code in qvc_data.get('centers', {}).keys():
        result[code] = get_qvc_capacity(code)
    
    return result


def is_qvc_country(nationality_code: str) -> bool:
    """Check if a nationality has QVC processing."""
    qvc_data = _load_qvc_capacity()
    if not qvc_data:
        return False
    return nationality_code in qvc_data.get('centers', {})


def get_qvc_summary() -> dict:
    """
    Get summary of all QVC capacity.
    
    Returns:
        Dict with total_daily_capacity, country breakdown, etc.
    """
    qvc_data = _load_qvc_capacity()
    if not qvc_data:
        return {
            'total_daily_capacity': 0,
            'total_monthly_capacity': 0,
            'countries': []
        }
    
    countries = []
    for code, data in qvc_data.get('centers', {}).items():
        countries.append({
            'code': code,
            'country': data['country'],
            'daily_capacity': data['total_daily_capacity'],
            'monthly_capacity': data['total_daily_capacity'] * 22,
            'center_count': len(data['centers']),
        })
    
    # Sort by daily capacity descending
    countries.sort(key=lambda x: -x['daily_capacity'])
    
    total_daily = sum(c['daily_capacity'] for c in countries)
    
    return {
        'total_daily_capacity': total_daily,
        'total_monthly_capacity': total_daily * 22,
        'country_count': len(countries),
        'countries': countries,
    }


# =============================================================================
# Non-QVC Countries: Outflow-Based Allocation
# =============================================================================

# Non-QVC countries that use outflow-based monthly capacity
NON_QVC_COUNTRIES = ['EGY', 'YEM', 'SYR', 'IRQ', 'IRN']

# Monthly outflow data calculated from 2024-2025 worker movement
# Left_2025 / 12 months = monthly average outflow
MONTHLY_OUTFLOW_DATA = {
    'EGY': {'left_2025': 8703, 'monthly_avg': 725, 'country': 'Egypt'},
    'YEM': {'left_2025': 848, 'monthly_avg': 71, 'country': 'Yemen'},
    'SYR': {'left_2025': 3415, 'monthly_avg': 285, 'country': 'Syria'},
    'IRQ': {'left_2025': 194, 'monthly_avg': 16, 'country': 'Iraq'},
    'IRN': {'left_2025': 750, 'monthly_avg': 63, 'country': 'Iran'},
}


def is_non_qvc_country(nationality_code: str) -> bool:
    """Check if a nationality uses outflow-based allocation (non-QVC)."""
    return nationality_code in NON_QVC_COUNTRIES


def get_outflow_capacity(nationality_code: str) -> Optional[dict]:
    """
    Get outflow-based monthly capacity for non-QVC countries.
    
    For countries without QVC centers, monthly capacity = previous month's outflow.
    This creates a replacement model where new workers replace those who left.
    
    Args:
        nationality_code: ISO 3-letter code (e.g., 'EGY')
        
    Returns:
        Outflow capacity dict or None if not a non-QVC country
    """
    if nationality_code not in NON_QVC_COUNTRIES:
        return None
    
    outflow_data = MONTHLY_OUTFLOW_DATA.get(nationality_code)
    if not outflow_data:
        return None
    
    # Get current stock and growth rate for additional context
    dashboard_data = get_real_dashboard_data(nationality_code)
    stock = dashboard_data.get('stock', 0) if dashboard_data else 0
    growth_rate = dashboard_data.get('growth_rate', 0) if dashboard_data else 0
    
    monthly_capacity = outflow_data['monthly_avg']
    annual_capacity = outflow_data['left_2025']
    
    return {
        'nationality_code': nationality_code,
        'country': outflow_data['country'],
        'capacity_type': 'outflow_based',
        'monthly_capacity': monthly_capacity,
        'annual_outflow': annual_capacity,
        'current_stock': stock,
        'growth_rate': growth_rate,
        'description': f"Based on {annual_capacity:,} workers who left in 2025 ({monthly_capacity:,}/month avg)",
    }


def get_all_non_qvc_capacity() -> dict:
    """
    Get outflow-based capacity for all non-QVC countries.
    
    Returns:
        Dict with nationality_code as key, capacity data as value
    """
    result = {}
    for code in NON_QVC_COUNTRIES:
        result[code] = get_outflow_capacity(code)
    return result


def get_non_qvc_summary() -> dict:
    """
    Get summary of all non-QVC country capacities.
    
    Returns:
        Dict with total monthly capacity, country breakdown, etc.
    """
    countries = []
    for code in NON_QVC_COUNTRIES:
        data = get_outflow_capacity(code)
        if data:
            countries.append({
                'code': code,
                'country': data['country'],
                'monthly_capacity': data['monthly_capacity'],
                'annual_outflow': data['annual_outflow'],
                'growth_rate': data['growth_rate'],
            })
    
    # Sort by monthly capacity descending
    countries.sort(key=lambda x: -x['monthly_capacity'])
    
    total_monthly = sum(c['monthly_capacity'] for c in countries)
    total_annual = sum(c['annual_outflow'] for c in countries)
    
    return {
        'total_monthly_capacity': total_monthly,
        'total_annual_outflow': total_annual,
        'country_count': len(countries),
        'countries': countries,
        'capacity_type': 'outflow_based',
        'description': 'Monthly capacity based on previous month outflow (replacement model)',
    }
