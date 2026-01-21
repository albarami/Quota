#!/usr/bin/env python
"""
Comprehensive Quota System Report for All 12 Restricted Nationalities.

Generates a detailed analysis using real ministry data from:
- 07_worker_stock.csv (worker records)
- 05_nationality_caps.csv (cap limits)
- 01_nationalities.csv (nationality reference)
- 02_professions.csv (profession reference)

Countries analyzed:
- QVC Countries (6): Bangladesh, India, Nepal, Pakistan, Philippines, Sri Lanka
- Non-QVC Countries (6): Egypt, Yemen, Syria, Iraq, Iran, Afghanistan
  - Outflow-Based (5): Egypt, Yemen, Syria, Iraq, Iran (Cap = Stock)
  - Standard Cap (1): Afghanistan (normal recommendations)
"""

import csv
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
REAL_DATA_DIR = PROJECT_ROOT / 'real_data'
REPORT_OUTPUT = PROJECT_ROOT / 'reports'

# Ensure reports directory exists
REPORT_OUTPUT.mkdir(exist_ok=True)

# ============================================================================
# CONFIGURATION - From System_Documentation.md
# ============================================================================

# Tier Classification Thresholds (Section 4)
TIER_1_THRESHOLD = 0.15  # >= 15% = Primary
TIER_2_THRESHOLD = 0.05  # >= 5% = Secondary
TIER_3_THRESHOLD = 0.01  # >= 1% = Minor

# Dominance Alert Thresholds (Section 6)
DOMINANCE_WATCH = 0.30    # 30-39% = WATCH
DOMINANCE_HIGH = 0.40     # 40-49% = HIGH
DOMINANCE_CRITICAL = 0.50 # >= 50% = CRITICAL
MIN_PROFESSION_SIZE = 200

# Headroom calculation factors (Section 5)
PENDING_APPROVAL_RATE = 0.8
OUTFLOW_CONFIDENCE_FACTOR = 0.75

# Exclude short-term workers (< 1 year)
MIN_EMPLOYMENT_DAYS = 365

# Country classifications
QVC_COUNTRIES = {'BGD', 'IND', 'NPL', 'PAK', 'PHL', 'LKA'}
# Note: Afghanistan (AFG) is NOT outflow-based - uses normal cap recommendations
NON_QVC_COUNTRIES = {'EGY', 'YEM', 'SYR', 'IRQ', 'IRN'}

# Nationality code mapping
NATIONALITY_CODES = {
    'EGY': '818', 'IND': '356', 'PAK': '586', 'NPL': '524',
    'BGD': '050', 'PHL': '608', 'IRN': '364', 'IRQ': '368',
    'YEM': '886', 'SYR': '760', 'AFG': '004', 'LKA': '144',
}
NUMERIC_TO_ISO = {v: k for k, v in NATIONALITY_CODES.items()}

# Growth rates from actual data
GROWTH_RATES = {
    'BGD': +0.92, 'PAK': +0.74, 'YEM': -1.26, 'IRQ': -6.38,
    'IRN': -6.79, 'NPL': -9.17, 'AFG': -9.47, 'EGY': -10.79,
    'IND': -11.95, 'SYR': -12.37, 'PHL': -13.34, 'LKA': -17.39,
}

# QVC Daily Capacity - loaded from qvc_capacity.json
def load_qvc_capacity():
    """Load QVC capacity from real data file."""
    qvc_file = REAL_DATA_DIR / 'qvc_capacity.json'
    if qvc_file.exists():
        import json
        with open(qvc_file, encoding='utf-8') as f:
            data = json.load(f)
        return {code: info['total_daily_capacity'] for code, info in data.get('centers', {}).items()}
    return {}

QVC_DAILY_CAPACITY = load_qvc_capacity()


def load_csv(filename):
    """Load a CSV file."""
    filepath = REAL_DATA_DIR / filename
    if not filepath.exists():
        return []
    with open(filepath, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_caps():
    """Load nationality caps."""
    rows = load_csv('05_nationality_caps.csv')
    caps = {}
    for row in rows:
        nat_code = row.get('nationality_code', '')
        if nat_code:
            caps[nat_code] = {
                'cap_limit': int(row.get('cap_limit', 0) or 0),
                'previous_cap': int(row.get('previous_cap', 0) or 0),
            }
    return caps


def load_nationalities():
    """Load nationality names."""
    rows = load_csv('01_nationalities.csv')
    return {row['code']: row.get('name', row['code']) for row in rows}


def load_professions():
    """Load profession names."""
    rows = load_csv('02_professions.csv')
    return {row['code']: row.get('name', f'Prof_{row["code"]}') for row in rows}


def is_long_term(emp_start_str, emp_end_str, state, today):
    """Check if worker has employment >= 1 year."""
    if not emp_start_str:
        return True
    try:
        emp_start = datetime.strptime(emp_start_str[:10], '%Y-%m-%d')
        if emp_end_str and state == 'OUT_COUNTRY':
            emp_end = datetime.strptime(emp_end_str[:10], '%Y-%m-%d')
        else:
            emp_end = today
        return (emp_end - emp_start).days >= MIN_EMPLOYMENT_DAYS
    except (ValueError, TypeError):
        return True


def process_worker_data():
    """Process all worker data and compute metrics for all 12 nationalities."""
    print("=" * 80)
    print("COMPREHENSIVE QUOTA SYSTEM REPORT")
    print("=" * 80)
    print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data Source: {REAL_DATA_DIR}")
    print()
    
    # Load reference data
    caps = load_caps()
    nationalities = load_nationalities()
    professions = load_professions()
    
    # Initialize data structures
    data = {}
    for iso_code in NATIONALITY_CODES:
        num_code = NATIONALITY_CODES[iso_code]
        data[iso_code] = {
            'name': nationalities.get(num_code, iso_code),
            'numeric_code': num_code,
            'is_qvc': iso_code in QVC_COUNTRIES,
            'growth_rate': GROWTH_RATES.get(iso_code, 0),
            'original_cap': caps.get(num_code, {}).get('cap_limit', 0),
            'previous_cap': caps.get(num_code, {}).get('previous_cap', 0),
            'in_country': 0,
            'out_country': 0,
            'left_2024': 0,
            'left_2025': 0,
            'joined_2024': 0,
            'joined_2025': 0,
            'profession_counts': defaultdict(int),
        }
    
    # Track global profession totals for dominance
    total_by_profession = defaultdict(int)
    
    # Process worker file
    worker_file = REAL_DATA_DIR / '07_worker_stock.csv'
    today = datetime.now()
    
    print("Processing worker data...")
    row_count = 0
    short_term_excluded = 0
    
    with open(worker_file, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_count += 1
            if row_count % 1000000 == 0:
                print(f"  Processed {row_count:,} rows...")
            
            nat_code = row.get('nationality_code', '')
            iso_code = NUMERIC_TO_ISO.get(nat_code)
            state = row.get('state', '').upper()
            prof_code = row.get('profession_code', 'Unknown')
            emp_start = row.get('employment_start', '')
            emp_end = row.get('employment_end', '')
            
            # Skip short-term workers
            if not is_long_term(emp_start, emp_end, state, today):
                short_term_excluded += 1
                continue
            
            # Track global profession totals (for dominance)
            if state in ('ACTIVE', 'IN_COUNTRY', ''):
                total_by_profession[prof_code] += 1
            
            # Only track our 12 nationalities
            if not iso_code:
                continue
            
            # Count by state
            if state in ('ACTIVE', 'IN_COUNTRY', ''):
                data[iso_code]['in_country'] += 1
                data[iso_code]['profession_counts'][prof_code] += 1
            elif state == 'OUT_COUNTRY':
                data[iso_code]['out_country'] += 1
                
                # Track when they left
                if emp_end:
                    try:
                        end_date = datetime.strptime(emp_end[:10], '%Y-%m-%d')
                        if end_date.year == 2024:
                            data[iso_code]['left_2024'] += 1
                        elif end_date.year == 2025:
                            data[iso_code]['left_2025'] += 1
                    except:
                        pass
            
            # Track when they joined
            if emp_start:
                try:
                    start_date = datetime.strptime(emp_start[:10], '%Y-%m-%d')
                    if start_date.year == 2024:
                        data[iso_code]['joined_2024'] += 1
                    elif start_date.year == 2025:
                        data[iso_code]['joined_2025'] += 1
                except:
                    pass
    
    print(f"  Total rows: {row_count:,}")
    print(f"  Short-term excluded: {short_term_excluded:,}")
    print()
    
    # Calculate derived metrics
    results = {'qvc': [], 'non_qvc': []}
    
    for iso_code, d in data.items():
        stock = d['in_country']
        original_cap = d['original_cap']
        growth_rate = d['growth_rate']
        is_qvc = d['is_qvc']
        
        # Apply Cap = Stock rule for non-QVC negative growth
        # EXCEPTION: Afghanistan (AFG) uses standard cap, NOT outflow-based
        is_outflow_based = not is_qvc and growth_rate < 0 and iso_code != 'AFG'
        effective_cap = stock if is_outflow_based else original_cap
        
        # Utilization
        utilization = (stock / effective_cap * 100) if effective_cap > 0 else 0
        
        # Headroom
        if is_outflow_based:
            headroom = 0
        elif effective_cap > 0:
            projected_outflow = int(stock * 0.015 * 3)
            headroom = max(0, effective_cap - stock + int(projected_outflow * OUTFLOW_CONFIDENCE_FACTOR))
        else:
            headroom = 0
        
        # Monthly outflow (average from 2024-2025)
        total_left = d['left_2024'] + d['left_2025']
        months = 23  # 12 months 2024 + 11 months 2025
        monthly_outflow = int(total_left / months) if months > 0 else 0
        
        # Dominance alerts - CHECK ALL PROFESSIONS (not just top 50)
        dominance_alerts = []
        total_this_nat = sum(d['profession_counts'].values())
        
        # Iterate through ALL professions this nationality works in
        for prof_code, count in d['profession_counts'].items():
            total_in_prof = total_by_profession.get(prof_code, 0)
            if total_in_prof >= MIN_PROFESSION_SIZE:
                dominance_share = count / total_in_prof
                if dominance_share >= DOMINANCE_WATCH:
                    level = 'CRITICAL' if dominance_share >= DOMINANCE_CRITICAL else \
                            'HIGH' if dominance_share >= DOMINANCE_HIGH else 'WATCH'
                    prof_name = professions.get(prof_code, prof_code)
                    dominance_alerts.append({
                        'profession': prof_name,
                        'level': level,
                        'share': dominance_share,
                        'count': count,
                        'total': total_in_prof,
                    })
        
        # Sort by share descending
        dominance_alerts.sort(key=lambda x: -x['share'])
        
        # Tier distribution
        tiers = {1: 0, 2: 0, 3: 0, 4: 0}
        for prof_code, count in d['profession_counts'].items():
            share = count / total_this_nat if total_this_nat > 0 else 0
            if share >= TIER_1_THRESHOLD:
                tiers[1] += 1
            elif share >= TIER_2_THRESHOLD:
                tiers[2] += 1
            elif share >= TIER_3_THRESHOLD:
                tiers[3] += 1
            else:
                tiers[4] += 1
        
        # QVC capacity
        qvc_daily = QVC_DAILY_CAPACITY.get(iso_code, 0) if is_qvc else 0
        qvc_monthly = qvc_daily * 22 if qvc_daily > 0 else 0
        
        result = {
            'code': iso_code,
            'name': d['name'],
            'is_qvc': is_qvc,
            'stock': stock,
            'original_cap': original_cap,
            'effective_cap': effective_cap,
            'is_outflow_based': is_outflow_based,
            'utilization': utilization,
            'headroom': headroom,
            'growth_rate': growth_rate,
            'left_2024': d['left_2024'],
            'left_2025': d['left_2025'],
            'joined_2024': d['joined_2024'],
            'joined_2025': d['joined_2025'],
            'monthly_outflow': monthly_outflow,
            'qvc_daily_capacity': qvc_daily,
            'qvc_monthly_capacity': qvc_monthly,
            'dominance_alerts': dominance_alerts,
            'tiers': tiers,
            'total_professions': len(d['profession_counts']),
        }
        
        if is_qvc:
            results['qvc'].append(result)
        else:
            results['non_qvc'].append(result)
    
    # Sort by stock descending
    results['qvc'].sort(key=lambda x: -x['stock'])
    results['non_qvc'].sort(key=lambda x: -x['stock'])
    
    return results


def print_report(results):
    """Print the comprehensive report."""
    
    # ========== QVC COUNTRIES ==========
    print("\n" + "=" * 80)
    print("SECTION 1: QVC COUNTRIES (Visa Center Processing)")
    print("=" * 80)
    print("These countries require QVC (Qatar Visa Center) processing in home country.")
    print()
    
    print(f"{'Country':<15} {'Stock':>12} {'Cap':>12} {'Util':>8} {'Headroom':>10} {'Growth':>8} {'QVC/Day':>8}")
    print("-" * 80)
    
    total_qvc_stock = 0
    total_qvc_cap = 0
    
    for r in results['qvc']:
        total_qvc_stock += r['stock']
        total_qvc_cap += r['effective_cap']
        print(f"{r['name'][:15]:<15} {r['stock']:>12,} {r['effective_cap']:>12,} "
              f"{r['utilization']:>7.1f}% {r['headroom']:>10,} {r['growth_rate']:>+7.1f}% {r['qvc_daily_capacity']:>8,}")
    
    print("-" * 80)
    total_qvc_util = (total_qvc_stock / total_qvc_cap * 100) if total_qvc_cap > 0 else 0
    print(f"{'TOTAL QVC':<15} {total_qvc_stock:>12,} {total_qvc_cap:>12,} {total_qvc_util:>7.1f}%")
    
    # QVC Flow Analysis
    print("\n" + "-" * 80)
    print("QVC FLOW ANALYSIS (2024-2025)")
    print("-" * 80)
    print(f"{'Country':<15} {'Left 2024':>12} {'Left 2025':>12} {'Joined 2024':>12} {'Joined 2025':>12} {'Monthly Out':>12}")
    print("-" * 80)
    
    for r in results['qvc']:
        print(f"{r['name'][:15]:<15} {r['left_2024']:>12,} {r['left_2025']:>12,} "
              f"{r['joined_2024']:>12,} {r['joined_2025']:>12,} {r['monthly_outflow']:>12,}")
    
    # ========== NON-QVC COUNTRIES ==========
    print("\n" + "=" * 80)
    print("SECTION 2: NON-QVC COUNTRIES (Direct Processing)")
    print("=" * 80)
    print("These countries do NOT require QVC processing.")
    print("Countries with NEGATIVE growth use OUTFLOW-BASED allocation (Cap = Stock).")
    print()
    
    print(f"{'Country':<15} {'Stock':>12} {'Cap':>12} {'Util':>8} {'Headroom':>10} {'Growth':>8} {'Type':<10}")
    print("-" * 80)
    
    total_non_qvc_stock = 0
    total_non_qvc_cap = 0
    
    for r in results['non_qvc']:
        total_non_qvc_stock += r['stock']
        total_non_qvc_cap += r['effective_cap']
        cap_type = "OUTFLOW" if r['is_outflow_based'] else "Standard"
        print(f"{r['name'][:15]:<15} {r['stock']:>12,} {r['effective_cap']:>12,} "
              f"{r['utilization']:>7.1f}% {r['headroom']:>10,} {r['growth_rate']:>+7.1f}% {cap_type:<10}")
    
    print("-" * 80)
    total_non_qvc_util = (total_non_qvc_stock / total_non_qvc_cap * 100) if total_non_qvc_cap > 0 else 0
    print(f"{'TOTAL NON-QVC':<15} {total_non_qvc_stock:>12,} {total_non_qvc_cap:>12,} {total_non_qvc_util:>7.1f}%")
    
    # Non-QVC Flow Analysis
    print("\n" + "-" * 80)
    print("NON-QVC FLOW ANALYSIS (2024-2025)")
    print("-" * 80)
    print(f"{'Country':<15} {'Left 2024':>12} {'Left 2025':>12} {'Joined 2024':>12} {'Joined 2025':>12} {'Monthly Out':>12}")
    print("-" * 80)
    
    for r in results['non_qvc']:
        print(f"{r['name'][:15]:<15} {r['left_2024']:>12,} {r['left_2025']:>12,} "
              f"{r['joined_2024']:>12,} {r['joined_2025']:>12,} {r['monthly_outflow']:>12,}")
    
    # ========== DOMINANCE ALERTS ==========
    print("\n" + "=" * 80)
    print("SECTION 3: DOMINANCE ALERTS")
    print("=" * 80)
    print("Formula: Dominance_Share = Nationality_Workers / Total_Workers_in_Profession")
    print(f"Minimum profession size: {MIN_PROFESSION_SIZE} workers")
    print("Thresholds: WATCH >= 30%, HIGH >= 40%, CRITICAL >= 50%")
    print()
    
    for category in ['qvc', 'non_qvc']:
        for r in results[category]:
            if r['dominance_alerts']:
                print(f"\n{r['name']} ({r['code']}) - {len(r['dominance_alerts'])} alerts:")
                for alert in sorted(r['dominance_alerts'], key=lambda x: -x['share'])[:10]:
                    print(f"  [{alert['level']:>8}] {alert['profession'][:40]:<40} "
                          f"{alert['share']*100:>5.1f}% ({alert['count']:,}/{alert['total']:,})")
    
    # ========== GRAND TOTALS ==========
    print("\n" + "=" * 80)
    print("SECTION 4: GRAND TOTALS (ALL 12 COUNTRIES)")
    print("=" * 80)
    
    grand_stock = total_qvc_stock + total_non_qvc_stock
    grand_cap = total_qvc_cap + total_non_qvc_cap
    grand_util = (grand_stock / grand_cap * 100) if grand_cap > 0 else 0
    
    total_alerts = sum(len(r['dominance_alerts']) for r in results['qvc'] + results['non_qvc'])
    
    print(f"""
    Total Workers (Long-term only):     {grand_stock:>15,}
    Total Effective Cap:                {grand_cap:>15,}
    Overall Utilization:                {grand_util:>14.1f}%
    
    QVC Countries:                      {len(results['qvc']):>15}
    Non-QVC Countries:                  {len(results['non_qvc']):>15}
    
    Outflow-Based Countries:            {sum(1 for r in results['non_qvc'] if r['is_outflow_based']):>15}
    Growing Countries:                  {sum(1 for r in results['qvc'] + results['non_qvc'] if r['growth_rate'] > 0):>15}
    Declining Countries:                {sum(1 for r in results['qvc'] + results['non_qvc'] if r['growth_rate'] < 0):>15}
    
    Total Dominance Alerts:             {total_alerts:>15}
    """)
    
    # ========== CAP RECOMMENDATIONS ==========
    print("=" * 80)
    print("SECTION 5: CAP RECOMMENDATIONS")
    print("=" * 80)
    print()
    
    print(f"{'Country':<15} {'Current Cap':>12} {'Recommended':>12} {'Change':>10} {'Reason':<25}")
    print("-" * 80)
    
    for r in results['qvc'] + results['non_qvc']:
        if r['is_outflow_based']:
            rec_cap = r['stock']
            change = rec_cap - r['original_cap']
            reason = "OUTFLOW-BASED (frozen)"
        elif r['growth_rate'] > 5:
            rec_cap = int(r['effective_cap'] * 1.10 * 1.05)  # Flexible + growth
            change = rec_cap - r['effective_cap']
            reason = "Growth > 5%"
        elif r['growth_rate'] < -5:
            rec_cap = int(r['effective_cap'] * 1.10 * 0.95)  # Moderate - decline
            change = rec_cap - r['effective_cap']
            reason = "Decline > 5%"
        else:
            rec_cap = int(r['effective_cap'] * 1.10)  # Moderate
            change = rec_cap - r['effective_cap']
            reason = "Standard moderate"
        
        alerts = len(r['dominance_alerts'])
        if alerts > 3:
            rec_cap = int(r['effective_cap'] * 1.05)  # Conservative
            change = rec_cap - r['effective_cap']
            reason = f"High alerts ({alerts})"
        
        print(f"{r['name'][:15]:<15} {r['effective_cap']:>12,} {rec_cap:>12,} {change:>+10,} {reason:<25}")
    
    print("\n" + "=" * 80)
    print("END OF REPORT")
    print("=" * 80)
    
    return results


def save_report_json(results):
    """Save report data as JSON."""
    output_file = REPORT_OUTPUT / f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nReport saved to: {output_file}")


if __name__ == '__main__':
    results = process_worker_data()
    print_report(results)
    save_report_json(results)
