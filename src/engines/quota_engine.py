"""
Quota Engine v4 - Core Calculation Module.

This is the SINGLE SOURCE OF TRUTH for all quota calculations.
Implements the Quota Allocation Methodology v4.0.

All formulas are based on:
- docs/Quota_Allocation_Methodology_v4.md

Key Principles:
1. Demand-driven caps using Joiners (positive growth) or Outflow (negative growth)
2. QVC capacity as hard constraint
3. No fallbacks or demo data - production only
"""

import csv
import json
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from functools import lru_cache


# =============================================================================
# CONSTANTS (from v4 methodology)
# =============================================================================

# Country Classifications
QVC_COUNTRIES = ['BGD', 'IND', 'NPL', 'PAK', 'PHL', 'LKA']
OUTFLOW_BASED = ['EGY', 'YEM', 'SYR', 'IRN', 'IRQ']
STANDARD_NON_QVC = ['AFG']

# QVC Annual Capacity (daily × 264 working days)
QVC_ANNUAL_CAPACITY = {
    'LKA': 39600,   # 150 × 264
    'BGD': 135960,  # 515 × 264
    'PAK': 97680,   # 370 × 264
    'IND': 212520,  # 805 × 264
    'NPL': 85800,   # 325 × 264
    'PHL': 73920    # 280 × 264
}

# Buffer Percentages
BUFFER_POSITIVE_QVC = 0.10      # 10% for positive growth QVC
BUFFER_NEGATIVE_QVC = 0.05      # 5% for negative growth QVC
BUFFER_STANDARD_NON_QVC = 0.05  # 5% for standard non-QVC

# Thresholds
MIN_EMPLOYMENT_DAYS = 365       # Long-term worker filter
MIN_PROFESSION_SIZE = 200       # Minimum for dominance calculation

# Tier Thresholds
TIER_1_THRESHOLD = 0.15     # >= 15% = Primary
TIER_2_THRESHOLD = 0.05     # >= 5% = Secondary
TIER_3_THRESHOLD = 0.01     # >= 1% = Minor
# < 1% = Tier 4 (Unusual)

# Dominance Thresholds
DOMINANCE_CRITICAL = 0.50
DOMINANCE_HIGH = 0.40
DOMINANCE_WATCH = 0.30

# Nationality Code Mapping
NATIONALITY_CODES = {
    'EGY': '818', 'IND': '356', 'PAK': '586', 'NPL': '524',
    'BGD': '050', 'PHL': '608', 'IRN': '364', 'IRQ': '368',
    'YEM': '886', 'SYR': '760', 'AFG': '004', 'LKA': '144',
}
NUMERIC_TO_ISO = {v: k for k, v in NATIONALITY_CODES.items()}

# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / 'real_data'

# Performance mode - use pre-computed summary for fast loading
USE_PRECOMPUTED = True  # Set to False for full CSV processing


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class QuotaMetrics:
    """Complete quota metrics for a nationality."""
    nationality_code: str
    nationality_name: str
    country_type: str  # 'QVC', 'OUTFLOW_BASED', 'STANDARD_NON_QVC'
    
    # Stock & Flow
    current_stock: int
    avg_annual_joiners: int
    avg_annual_outflow: int
    joined_2024: int
    joined_2025: int
    left_2024: int
    left_2025: int
    
    # Growth
    growth_direction: str  # 'POSITIVE' or 'NEGATIVE'
    growth_rate: float
    net_growth: int
    
    # Demand
    demand_basis: str  # 'Joiners' or 'Outflow'
    demand_value: int
    buffer_pct: float
    buffer_value: int
    
    # Cap Calculation
    desired_cap: int
    recommended_cap: int
    
    # QVC Constraint (QVC countries only)
    qvc_annual_capacity: Optional[int]
    net_qvc_capacity: Optional[int]
    max_achievable_cap: Optional[int]
    is_qvc_constrained: bool
    qvc_utilization_pct: Optional[float]
    
    # Derived Metrics
    headroom: int
    utilization_pct: float
    
    # Monthly allocation (for outflow-based)
    monthly_allocation: Optional[int]


@dataclass
class TierClassification:
    """Tier classification for a profession within a nationality."""
    profession_code: str
    profession_name: str
    worker_count: int
    tier_share: float  # Share within nationality
    tier_level: int  # 1, 2, 3, or 4


@dataclass
class DominanceAlert:
    """Dominance alert for a nationality-profession pair."""
    profession_code: str
    profession_name: str
    nationality_workers: int
    total_in_profession: int
    dominance_share: float
    alert_level: str  # 'CRITICAL', 'HIGH', 'WATCH', 'OK'
    is_blocking: bool


# =============================================================================
# DATA LOADING
# =============================================================================

@lru_cache(maxsize=1)
def _load_workers() -> list[dict]:
    """Load worker stock data from CSV. Cached for performance."""
    filepath = DATA_DIR / '07_worker_stock.csv'
    if not filepath.exists():
        raise FileNotFoundError(f"Worker stock file not found: {filepath}")
    
    workers = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            workers.append(row)
    return workers


@lru_cache(maxsize=1)
def _load_nationalities() -> dict[str, str]:
    """Load nationality code to name mapping."""
    filepath = DATA_DIR / '01_nationalities.csv'
    if not filepath.exists():
        return {}
    
    mapping = {}
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get('code', '').strip()
            name = row.get('name', '').strip()
            if code and name:
                mapping[code] = name
    return mapping


@lru_cache(maxsize=1)
def _load_professions() -> dict[str, str]:
    """Load profession code to name mapping."""
    filepath = DATA_DIR / '02_professions.csv'
    if not filepath.exists():
        return {}
    
    mapping = {}
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get('code', '').strip()
            name = row.get('name', row.get('name_en', '')).strip()
            if code:
                mapping[code] = name or f'Profession_{code}'
    return mapping


@lru_cache(maxsize=1)
def _load_qvc_capacity() -> dict:
    """Load QVC capacity data from JSON."""
    filepath = DATA_DIR / 'qvc_capacity.json'
    if not filepath.exists():
        return {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_precomputed_summary() -> dict:
    """Load pre-computed nationality summary for fast performance."""
    filepath = DATA_DIR / 'summary_by_nationality.json'
    if not filepath.exists():
        return {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('nationalities', {})


@lru_cache(maxsize=1)
def _load_growth_by_year() -> dict:
    """Load pre-computed growth data."""
    filepath = DATA_DIR / 'growth_by_year.json'
    if not filepath.exists():
        return {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def clear_cache():
    """Clear all cached data. Call when data files change."""
    _load_workers.cache_clear()
    _load_nationalities.cache_clear()
    _load_professions.cache_clear()
    _load_qvc_capacity.cache_clear()
    _load_precomputed_summary.cache_clear()
    _load_growth_by_year.cache_clear()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_numeric_code(iso_code: str) -> str:
    """Convert ISO 3-letter code to numeric code."""
    return NATIONALITY_CODES.get(iso_code, iso_code)


def _get_iso_code(numeric_code: str) -> str:
    """Convert numeric code to ISO 3-letter code."""
    # Handle leading zeros
    clean_code = numeric_code.lstrip('0') or '0'
    for num, iso in NUMERIC_TO_ISO.items():
        if num.lstrip('0') == clean_code:
            return iso
    return numeric_code


def _parse_date(date_str: str) -> Optional[date]:
    """Parse date string to date object."""
    if not date_str:
        return None
    try:
        # Handle various formats
        date_str = date_str.strip()[:10]  # Take first 10 chars
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _is_long_term(worker: dict, reference_date: date = None) -> bool:
    """Check if worker has employment duration >= 365 days."""
    if reference_date is None:
        reference_date = date.today()
    
    emp_start = _parse_date(worker.get('employment_start', ''))
    emp_end = _parse_date(worker.get('employment_end', ''))
    
    if not emp_start:
        return True  # Include if no start date
    
    # Use employment_end if present, otherwise today
    end_date = emp_end if emp_end else reference_date
    duration = (end_date - emp_start).days
    
    return duration >= MIN_EMPLOYMENT_DAYS


def _get_country_type(iso_code: str) -> str:
    """Determine country type for a nationality."""
    if iso_code in QVC_COUNTRIES:
        return 'QVC'
    elif iso_code in OUTFLOW_BASED:
        return 'OUTFLOW_BASED'
    elif iso_code in STANDARD_NON_QVC:
        return 'STANDARD_NON_QVC'
    else:
        return 'UNKNOWN'


# =============================================================================
# CORE CALCULATIONS
# =============================================================================

def calculate_stock(iso_code: str) -> int:
    """
    Calculate current stock for a nationality.
    
    Stock = COUNT workers WHERE:
        - nationality matches
        - status = 'IN_COUNTRY'
        - employment_duration >= 365 days
    """
    workers = _load_workers()
    numeric_code = _get_numeric_code(iso_code)
    
    count = 0
    for w in workers:
        w_nat = w.get('nationality_code', '').strip().strip('"')
        state = w.get('state', '').strip().upper()
        
        # Match nationality (handle leading zeros)
        if w_nat.lstrip('0') != numeric_code.lstrip('0'):
            continue
        
        # Only IN_COUNTRY workers
        if state not in ('IN_COUNTRY', 'ACTIVE', ''):
            continue
        
        # Only long-term workers
        if not _is_long_term(w):
            continue
        
        count += 1
    
    return count


def calculate_joiners(iso_code: str, year: int) -> int:
    """
    Calculate workers who joined in a specific year.
    
    Joiners = COUNT workers WHERE employment_start is in year
    """
    workers = _load_workers()
    numeric_code = _get_numeric_code(iso_code)
    
    count = 0
    for w in workers:
        w_nat = w.get('nationality_code', '').strip().strip('"')
        
        # Match nationality
        if w_nat.lstrip('0') != numeric_code.lstrip('0'):
            continue
        
        # Only long-term workers
        if not _is_long_term(w):
            continue
        
        # Check employment_start year
        emp_start = _parse_date(w.get('employment_start', ''))
        if emp_start and emp_start.year == year:
            count += 1
    
    return count


def calculate_outflow(iso_code: str, year: int) -> int:
    """
    Calculate workers who left in a specific year.
    
    Outflow = COUNT workers WHERE employment_end is in year
    """
    workers = _load_workers()
    numeric_code = _get_numeric_code(iso_code)
    
    count = 0
    for w in workers:
        w_nat = w.get('nationality_code', '').strip().strip('"')
        
        # Match nationality
        if w_nat.lstrip('0') != numeric_code.lstrip('0'):
            continue
        
        # Only long-term workers
        if not _is_long_term(w):
            continue
        
        # Check employment_end year
        emp_end = _parse_date(w.get('employment_end', ''))
        if emp_end and emp_end.year == year:
            count += 1
    
    return count


def calculate_growth_rate(iso_code: str) -> tuple[float, int, int]:
    """
    Calculate year-over-year growth rate.
    
    Returns: (growth_rate_pct, total_2024, total_2025)
    
    Formula: Growth = (Total_2025 - Total_2024) / Total_2024 × 100
    """
    workers = _load_workers()
    numeric_code = _get_numeric_code(iso_code)
    
    # Count workers active in each year
    total_2024 = 0
    total_2025 = 0
    
    for w in workers:
        w_nat = w.get('nationality_code', '').strip().strip('"')
        
        # Match nationality
        if w_nat.lstrip('0') != numeric_code.lstrip('0'):
            continue
        
        # Only long-term workers
        if not _is_long_term(w):
            continue
        
        emp_start = _parse_date(w.get('employment_start', ''))
        emp_end = _parse_date(w.get('employment_end', ''))
        
        if not emp_start:
            continue
        
        # Worker was active in 2024 if:
        # - Started on or before Dec 31, 2024
        # - Ended on or after Jan 1, 2024 (or still active)
        if emp_start <= date(2024, 12, 31):
            if emp_end is None or emp_end >= date(2024, 1, 1):
                total_2024 += 1
        
        # Worker was active in 2025 if:
        # - Started on or before Dec 31, 2025
        # - Ended on or after Jan 1, 2025 (or still active)
        if emp_start <= date(2025, 12, 31):
            if emp_end is None or emp_end >= date(2025, 1, 1):
                total_2025 += 1
    
    if total_2024 > 0:
        growth_rate = ((total_2025 - total_2024) / total_2024) * 100
    else:
        growth_rate = 0.0
    
    return growth_rate, total_2024, total_2025


def calculate_recommended_cap(iso_code: str) -> QuotaMetrics:
    """
    Calculate recommended cap using v4 methodology.
    
    This is the main calculation function implementing the complete v4 formula.
    """
    # Get nationality info
    nationalities = _load_nationalities()
    numeric_code = _get_numeric_code(iso_code)
    nat_name = nationalities.get(numeric_code, iso_code)
    country_type = _get_country_type(iso_code)
    
    # Calculate stock
    stock = calculate_stock(iso_code)
    
    # Calculate joiners and outflow
    joined_2024 = calculate_joiners(iso_code, 2024)
    joined_2025 = calculate_joiners(iso_code, 2025)
    left_2024 = calculate_outflow(iso_code, 2024)
    left_2025 = calculate_outflow(iso_code, 2025)
    
    avg_joiners = (joined_2024 + joined_2025) // 2
    avg_outflow = (left_2024 + left_2025) // 2
    
    # Calculate growth
    growth_rate, _, _ = calculate_growth_rate(iso_code)
    is_positive_growth = avg_joiners > avg_outflow
    net_growth = avg_joiners - avg_outflow
    growth_direction = 'POSITIVE' if is_positive_growth else 'NEGATIVE'
    
    # Initialize QVC-related variables
    qvc_annual = None
    net_qvc = None
    max_achievable = None
    is_constrained = False
    qvc_utilization = None
    monthly_allocation = None
    
    # =========================================================================
    # CALCULATE RECOMMENDED CAP BY COUNTRY TYPE
    # =========================================================================
    
    if country_type == 'QVC':
        # QVC Countries: Apply QVC constraint
        qvc_annual = QVC_ANNUAL_CAPACITY.get(iso_code, 0)
        net_qvc = qvc_annual - avg_outflow
        max_achievable = stock + net_qvc
        
        # Determine demand basis and buffer
        if is_positive_growth:
            demand_basis = 'Joiners'
            demand_value = avg_joiners
            buffer_pct = BUFFER_POSITIVE_QVC
        else:
            demand_basis = 'Outflow'
            demand_value = avg_outflow
            buffer_pct = BUFFER_NEGATIVE_QVC
        
        buffer_value = int(stock * buffer_pct)
        desired_cap = stock + demand_value + buffer_value
        
        # Apply QVC constraint
        recommended_cap = min(desired_cap, max_achievable)
        is_constrained = desired_cap > max_achievable
        
        # QVC utilization
        qvc_utilization = (avg_outflow / qvc_annual * 100) if qvc_annual > 0 else 0
        
    elif country_type == 'OUTFLOW_BASED':
        # Non-QVC Outflow-Based: Cap frozen at stock
        demand_basis = 'Frozen'
        demand_value = 0
        buffer_pct = 0.0
        buffer_value = 0
        desired_cap = stock
        recommended_cap = stock
        monthly_allocation = avg_outflow // 12
        
    elif country_type == 'STANDARD_NON_QVC':
        # Standard Non-QVC (Afghanistan): Use standard formula
        if is_positive_growth:
            demand_basis = 'Joiners'
            demand_value = avg_joiners
        else:
            demand_basis = 'Outflow'
            demand_value = avg_outflow
        
        buffer_pct = BUFFER_STANDARD_NON_QVC
        buffer_value = int(stock * buffer_pct)
        desired_cap = stock + demand_value + buffer_value
        recommended_cap = desired_cap
        
    else:
        # Unknown country type - use conservative approach
        demand_basis = 'Outflow'
        demand_value = avg_outflow
        buffer_pct = BUFFER_STANDARD_NON_QVC
        buffer_value = int(stock * buffer_pct)
        desired_cap = stock + demand_value + buffer_value
        recommended_cap = desired_cap
    
    # Calculate derived metrics
    headroom = recommended_cap - stock
    utilization = (stock / recommended_cap * 100) if recommended_cap > 0 else 100.0
    
    return QuotaMetrics(
        nationality_code=iso_code,
        nationality_name=nat_name,
        country_type=country_type,
        current_stock=stock,
        avg_annual_joiners=avg_joiners,
        avg_annual_outflow=avg_outflow,
        joined_2024=joined_2024,
        joined_2025=joined_2025,
        left_2024=left_2024,
        left_2025=left_2025,
        growth_direction=growth_direction,
        growth_rate=round(growth_rate, 2),
        net_growth=net_growth,
        demand_basis=demand_basis,
        demand_value=demand_value,
        buffer_pct=buffer_pct,
        buffer_value=buffer_value,
        desired_cap=desired_cap,
        recommended_cap=recommended_cap,
        qvc_annual_capacity=qvc_annual,
        net_qvc_capacity=net_qvc,
        max_achievable_cap=max_achievable,
        is_qvc_constrained=is_constrained,
        qvc_utilization_pct=round(qvc_utilization, 1) if qvc_utilization else None,
        headroom=headroom,
        utilization_pct=round(utilization, 1),
        monthly_allocation=monthly_allocation,
    )


def calculate_tier_classification(iso_code: str) -> list[TierClassification]:
    """
    Calculate tier classification for all professions of a nationality.
    
    Tier Share = Workers_in_Profession / Total_Workers_of_Nationality × 100
    """
    workers = _load_workers()
    professions = _load_professions()
    numeric_code = _get_numeric_code(iso_code)
    
    # Count workers by profession
    profession_counts: dict[str, int] = {}
    total_workers = 0
    
    for w in workers:
        w_nat = w.get('nationality_code', '').strip().strip('"')
        state = w.get('state', '').strip().upper()
        
        # Match nationality
        if w_nat.lstrip('0') != numeric_code.lstrip('0'):
            continue
        
        # Only IN_COUNTRY workers
        if state not in ('IN_COUNTRY', 'ACTIVE', ''):
            continue
        
        # Only long-term workers
        if not _is_long_term(w):
            continue
        
        prof_code = w.get('profession_code', '').strip().strip('"')
        profession_counts[prof_code] = profession_counts.get(prof_code, 0) + 1
        total_workers += 1
    
    # Classify into tiers
    classifications = []
    for prof_code, count in sorted(profession_counts.items(), key=lambda x: -x[1]):
        tier_share = count / total_workers if total_workers > 0 else 0
        
        if tier_share >= TIER_1_THRESHOLD:
            tier_level = 1
        elif tier_share >= TIER_2_THRESHOLD:
            tier_level = 2
        elif tier_share >= TIER_3_THRESHOLD:
            tier_level = 3
        else:
            tier_level = 4
        
        classifications.append(TierClassification(
            profession_code=prof_code,
            profession_name=professions.get(prof_code, f'Code_{prof_code}'),
            worker_count=count,
            tier_share=round(tier_share, 4),
            tier_level=tier_level,
        ))
    
    return classifications


def calculate_dominance_alerts(iso_code: str) -> list[DominanceAlert]:
    """
    Calculate dominance alerts for a nationality.
    
    Dominance Share = Nationality_Workers_in_Profession / Total_Workers_in_Profession × 100
    Only applies to professions with >= 200 total workers.
    """
    workers = _load_workers()
    professions = _load_professions()
    numeric_code = _get_numeric_code(iso_code)
    
    # First pass: count total workers per profession (all nationalities)
    total_by_profession: dict[str, int] = {}
    
    for w in workers:
        state = w.get('state', '').strip().upper()
        
        # Only IN_COUNTRY workers
        if state not in ('IN_COUNTRY', 'ACTIVE', ''):
            continue
        
        # Only long-term workers
        if not _is_long_term(w):
            continue
        
        prof_code = w.get('profession_code', '').strip().strip('"')
        total_by_profession[prof_code] = total_by_profession.get(prof_code, 0) + 1
    
    # Second pass: count this nationality's workers per profession
    nat_by_profession: dict[str, int] = {}
    
    for w in workers:
        w_nat = w.get('nationality_code', '').strip().strip('"')
        state = w.get('state', '').strip().upper()
        
        # Match nationality
        if w_nat.lstrip('0') != numeric_code.lstrip('0'):
            continue
        
        # Only IN_COUNTRY workers
        if state not in ('IN_COUNTRY', 'ACTIVE', ''):
            continue
        
        # Only long-term workers
        if not _is_long_term(w):
            continue
        
        prof_code = w.get('profession_code', '').strip().strip('"')
        nat_by_profession[prof_code] = nat_by_profession.get(prof_code, 0) + 1
    
    # Calculate dominance and generate alerts
    alerts = []
    
    for prof_code, nat_count in nat_by_profession.items():
        total_count = total_by_profession.get(prof_code, 0)
        
        # Skip small professions
        if total_count < MIN_PROFESSION_SIZE:
            continue
        
        dominance_share = nat_count / total_count if total_count > 0 else 0
        
        # Determine alert level
        if dominance_share >= DOMINANCE_CRITICAL:
            alert_level = 'CRITICAL'
            is_blocking = True
        elif dominance_share >= DOMINANCE_HIGH:
            alert_level = 'HIGH'
            is_blocking = False
        elif dominance_share >= DOMINANCE_WATCH:
            alert_level = 'WATCH'
            is_blocking = False
        else:
            continue  # No alert
        
        alerts.append(DominanceAlert(
            profession_code=prof_code,
            profession_name=professions.get(prof_code, f'Code_{prof_code}'),
            nationality_workers=nat_count,
            total_in_profession=total_count,
            dominance_share=round(dominance_share, 4),
            alert_level=alert_level,
            is_blocking=is_blocking,
        ))
    
    # Sort by dominance share descending
    alerts.sort(key=lambda x: -x.dominance_share)
    
    return alerts


def get_all_metrics_from_precomputed(iso_code: str) -> dict:
    """
    Get metrics using pre-computed summary data for fast performance.
    
    This uses the quota_summary.json or summary_by_nationality.json file.
    If v4 metrics are present (avg_annual_joiners, avg_annual_outflow), uses them directly.
    Otherwise falls back to estimation.
    """
    summary = _load_precomputed_summary()
    growth_data = _load_growth_by_year()
    
    if iso_code not in summary:
        raise ValueError(f"No pre-computed data for {iso_code}")
    
    nat_data = summary[iso_code]
    country_type = _get_country_type(iso_code)
    
    # Extract base metrics
    stock = nat_data.get('current_stock', nat_data.get('in_country', nat_data.get('stock', 0)))
    growth_rate = nat_data.get('growth_rate', 0)
    
    # Check if v4 metrics are already computed in summary
    if 'avg_annual_joiners' in nat_data and 'avg_annual_outflow' in nat_data:
        # Use exact v4 values from summary
        avg_joiners = nat_data['avg_annual_joiners']
        avg_outflow = nat_data['avg_annual_outflow']
    else:
        # Fall back to estimation from projected_outflow
        projected_monthly = nat_data.get('projected_outflow', 0)
        avg_outflow = projected_monthly * 12  # Annualize
        
        # Get year-over-year data if available
        year_data = growth_data.get(iso_code, {})
        total_2024 = year_data.get('total_2024', 0)
        total_2025 = year_data.get('total_2025', 0)
        
        # Estimate joiners based on growth pattern
        avg_joiners = max(0, int(avg_outflow * (1 + growth_rate / 100)))
    
    # Determine growth direction
    is_positive_growth = avg_joiners > avg_outflow
    growth_direction = 'POSITIVE' if is_positive_growth else 'NEGATIVE'
    net_growth = avg_joiners - avg_outflow
    
    # Initialize QVC variables
    qvc_annual = None
    net_qvc = None
    max_achievable = None
    is_constrained = False
    qvc_utilization = None
    monthly_allocation = None
    
    # Apply v4 cap calculation
    if country_type == 'QVC':
        qvc_annual = QVC_ANNUAL_CAPACITY.get(iso_code, 0)
        net_qvc = qvc_annual - avg_outflow
        max_achievable = stock + net_qvc
        
        if is_positive_growth:
            demand_basis = 'Joiners'
            demand_value = avg_joiners
            buffer_pct = BUFFER_POSITIVE_QVC
        else:
            demand_basis = 'Outflow'
            demand_value = avg_outflow
            buffer_pct = BUFFER_NEGATIVE_QVC
        
        buffer_value = int(stock * buffer_pct)
        desired_cap = stock + demand_value + buffer_value
        recommended_cap = min(desired_cap, max_achievable)
        is_constrained = desired_cap > max_achievable
        qvc_utilization = (avg_outflow / qvc_annual * 100) if qvc_annual > 0 else 0
        
    elif country_type == 'OUTFLOW_BASED':
        demand_basis = 'Frozen'
        demand_value = 0
        buffer_pct = 0.0
        buffer_value = 0
        desired_cap = stock
        recommended_cap = stock
        monthly_allocation = avg_outflow // 12
        
    else:  # STANDARD_NON_QVC
        if is_positive_growth:
            demand_basis = 'Joiners'
            demand_value = avg_joiners
        else:
            demand_basis = 'Outflow'
            demand_value = avg_outflow
        
        buffer_pct = BUFFER_STANDARD_NON_QVC
        buffer_value = int(stock * buffer_pct)
        desired_cap = stock + demand_value + buffer_value
        recommended_cap = desired_cap
    
    headroom = recommended_cap - stock
    utilization = (stock / recommended_cap * 100) if recommended_cap > 0 else 100.0
    
    # Get tier summary from pre-computed data
    tier_data = nat_data.get('tier_summary', {})
    tier_summary = {}
    for level in ['1', '2', '3', '4']:
        tier_info = tier_data.get(level, {})
        tier_summary[level] = {
            'profession_count': tier_info.get('profession_count', 0),
            'worker_count': tier_info.get('worker_count', 0),
            'share': tier_info.get('share', 0),
            'top_professions': tier_info.get('top_professions', [])[:5],
        }
    
    # Get dominance alerts from pre-computed data
    dominance_alerts = nat_data.get('dominance_alerts', [])
    alert_list = []
    for alert in dominance_alerts[:10]:
        alert_list.append({
            'profession_code': alert.get('profession_id', ''),
            'profession_name': alert.get('profession_name', ''),
            'nationality_workers': alert.get('nationality_workers', 0),
            'total_in_profession': alert.get('total_in_profession', 0),
            'share_pct': alert.get('share_pct', 0),
            'alert_level': alert.get('alert_level', 'OK'),
            'is_blocking': alert.get('is_blocking', False),
        })
    
    # Get yearly data if available in summary
    joined_2024 = nat_data.get('joined_2024', 0)
    joined_2025 = nat_data.get('joined_2025', 0)
    left_2024 = nat_data.get('left_2024', 0)
    left_2025 = nat_data.get('left_2025', 0)
    
    # Fall back to estimation if not in summary
    if not joined_2024 and not joined_2025:
        joined_2024 = avg_joiners
        joined_2025 = avg_joiners
    if not left_2024 and not left_2025:
        left_2024 = avg_outflow
        left_2025 = avg_outflow
    
    return {
        'nationality_code': iso_code,
        'nationality_name': nat_data.get('name', iso_code),
        'country_type': country_type,
        'current_stock': stock,
        'stock': stock,
        'avg_annual_joiners': avg_joiners,
        'avg_annual_outflow': avg_outflow,
        'joined_2024': joined_2024,
        'joined_2025': joined_2025,
        'left_2024': left_2024,
        'left_2025': left_2025,
        'growth_direction': growth_direction,
        'growth_rate': round(growth_rate, 2),
        'net_growth': net_growth,
        'demand_basis': demand_basis,
        'demand_value': demand_value,
        'buffer_pct': buffer_pct,
        'buffer_value': buffer_value,
        'desired_cap': desired_cap,
        'recommended_cap': recommended_cap,
        'cap': recommended_cap,
        'qvc_annual_capacity': qvc_annual,
        'net_qvc_capacity': net_qvc,
        'max_achievable_cap': max_achievable,
        'is_qvc_constrained': is_constrained,
        'qvc_utilization_pct': round(qvc_utilization, 1) if qvc_utilization else None,
        'headroom': headroom,
        'utilization_pct': round(utilization, 1),
        'monthly_allocation': monthly_allocation,
        'tier_summary': tier_summary,
        'dominance_alerts': alert_list,
        'alert_count': len(alert_list),
        'has_critical': any(a.get('alert_level') == 'CRITICAL' for a in alert_list),
        'last_updated': datetime.now().isoformat(),
        'formula_version': '4.0',
    }


def get_all_metrics(iso_code: str) -> dict:
    """
    Get all metrics for a nationality as a dictionary.
    
    This is the main function to call from the dashboard/API.
    Returns a complete dictionary with all v4 metrics.
    
    Uses pre-computed summary for fast performance when available.
    Falls back to full CSV processing if needed.
    """
    # Use pre-computed data for fast performance
    if USE_PRECOMPUTED:
        try:
            return get_all_metrics_from_precomputed(iso_code)
        except (ValueError, KeyError):
            pass  # Fall through to full calculation
    
    # Full calculation from CSV (slower but comprehensive)
    metrics = calculate_recommended_cap(iso_code)
    tiers = calculate_tier_classification(iso_code)
    alerts = calculate_dominance_alerts(iso_code)
    
    # Build tier summary
    tier_summary = {1: [], 2: [], 3: [], 4: []}
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    tier_workers = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for t in tiers:
        tier_summary[t.tier_level].append({
            'code': t.profession_code,
            'name': t.profession_name,
            'count': t.worker_count,
            'share': t.tier_share,
        })
        tier_counts[t.tier_level] += 1
        tier_workers[t.tier_level] += t.worker_count
    
    # Limit to top 5 per tier
    for level in tier_summary:
        tier_summary[level] = tier_summary[level][:5]
    
    # Build alerts list
    alert_list = []
    for a in alerts[:10]:  # Limit to top 10
        alert_list.append({
            'profession_code': a.profession_code,
            'profession_name': a.profession_name,
            'nationality_workers': a.nationality_workers,
            'total_in_profession': a.total_in_profession,
            'share_pct': a.dominance_share,
            'alert_level': a.alert_level,
            'is_blocking': a.is_blocking,
        })
    
    return {
        # Identity
        'nationality_code': metrics.nationality_code,
        'nationality_name': metrics.nationality_name,
        'country_type': metrics.country_type,
        
        # Stock & Flow
        'current_stock': metrics.current_stock,
        'stock': metrics.current_stock,  # Alias for compatibility
        'avg_annual_joiners': metrics.avg_annual_joiners,
        'avg_annual_outflow': metrics.avg_annual_outflow,
        'joined_2024': metrics.joined_2024,
        'joined_2025': metrics.joined_2025,
        'left_2024': metrics.left_2024,
        'left_2025': metrics.left_2025,
        
        # Growth
        'growth_direction': metrics.growth_direction,
        'growth_rate': metrics.growth_rate,
        'net_growth': metrics.net_growth,
        
        # Demand
        'demand_basis': metrics.demand_basis,
        'demand_value': metrics.demand_value,
        'buffer_pct': metrics.buffer_pct,
        'buffer_value': metrics.buffer_value,
        
        # Cap Calculation
        'desired_cap': metrics.desired_cap,
        'recommended_cap': metrics.recommended_cap,
        'cap': metrics.recommended_cap,  # Alias for compatibility
        
        # QVC Constraint
        'qvc_annual_capacity': metrics.qvc_annual_capacity,
        'net_qvc_capacity': metrics.net_qvc_capacity,
        'max_achievable_cap': metrics.max_achievable_cap,
        'is_qvc_constrained': metrics.is_qvc_constrained,
        'qvc_utilization_pct': metrics.qvc_utilization_pct,
        
        # Derived
        'headroom': metrics.headroom,
        'utilization_pct': metrics.utilization_pct,
        'monthly_allocation': metrics.monthly_allocation,
        
        # Tiers
        'tier_summary': {
            str(level): {
                'profession_count': tier_counts[level],
                'worker_count': tier_workers[level],
                'share': tier_workers[level] / metrics.current_stock if metrics.current_stock > 0 else 0,
                'top_professions': tier_summary[level],
            }
            for level in [1, 2, 3, 4]
        },
        
        # Dominance Alerts
        'dominance_alerts': alert_list,
        'alert_count': len(alert_list),
        'has_critical': any(a['alert_level'] == 'CRITICAL' for a in alert_list),
        
        # Metadata
        'last_updated': datetime.now().isoformat(),
        'formula_version': '4.0',
    }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_all_nationalities() -> list[str]:
    """Get list of all restricted nationality codes."""
    return QVC_COUNTRIES + OUTFLOW_BASED + STANDARD_NON_QVC


def is_qvc_country(iso_code: str) -> bool:
    """Check if nationality is a QVC country."""
    return iso_code in QVC_COUNTRIES


def is_outflow_based(iso_code: str) -> bool:
    """Check if nationality uses outflow-based allocation."""
    return iso_code in OUTFLOW_BASED


def get_qvc_capacity_details(iso_code: str) -> Optional[dict]:
    """Get QVC capacity details for a nationality."""
    if iso_code not in QVC_COUNTRIES:
        return None
    
    qvc_data = _load_qvc_capacity()
    centers = qvc_data.get('centers', {})
    
    if iso_code not in centers:
        return None
    
    center_data = centers[iso_code]
    daily = center_data.get('total_daily_capacity', 0)
    
    return {
        'country': center_data.get('country', iso_code),
        'daily_capacity': daily,
        'monthly_capacity': daily * 22,  # 22 working days
        'annual_capacity': daily * 264,  # 264 working days
        'centers': center_data.get('centers', []),
    }


if __name__ == '__main__':
    # Test the engine
    print("Testing Quota Engine v4...")
    print("=" * 60)
    
    for code in ['IND', 'BGD', 'EGY', 'AFG']:
        print(f"\n{code}:")
        metrics = get_all_metrics(code)
        print(f"  Stock: {metrics['current_stock']:,}")
        print(f"  Growth: {metrics['growth_direction']} ({metrics['growth_rate']:+.1f}%)")
        print(f"  Demand Basis: {metrics['demand_basis']}")
        print(f"  Desired Cap: {metrics['desired_cap']:,}")
        print(f"  Recommended Cap: {metrics['recommended_cap']:,}")
        if metrics['is_qvc_constrained']:
            print(f"  QVC CONSTRAINED (Max: {metrics['max_achievable_cap']:,})")
        print(f"  Alerts: {metrics['alert_count']}")
