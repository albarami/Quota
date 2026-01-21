#!/usr/bin/env python
"""
Create summary data files for faster Streamlit loading.

This script pre-computes summaries from the large worker_stock.csv file
to enable fast dashboard loading.

IMPORTANT: Implements exact formulas from System_Documentation.md:
- Tier Classification: Section 4, 11.A (profession share within nationality)
- Dominance Alerts: Section 6, 11.D (nationality share within profession)
- Headroom: Section 5, 11.B
- Utilization: Section 5, 11.C
"""

import csv
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

REAL_DATA_DIR = project_root / 'real_data'
SUMMARY_FILE = REAL_DATA_DIR / 'summary_by_nationality.json'

# ============================================================================
# CONFIGURATION - From System_Documentation.md Section 12 Parameter Registry
# ============================================================================

# Tier Classification Thresholds (Section 4)
TIER_1_THRESHOLD = 0.15  # >= 15% = Primary
TIER_2_THRESHOLD = 0.05  # >= 5% = Secondary
TIER_3_THRESHOLD = 0.01  # >= 1% = Minor
# < 1% = Unusual (Tier 4)

# Dominance Alert Thresholds (Section 6)
DOMINANCE_WATCH = 0.30    # 30-39% = WATCH
DOMINANCE_HIGH = 0.40     # 40-49% = HIGH
DOMINANCE_CRITICAL = 0.50 # >= 50% = CRITICAL

# Minimum profession size for dominance analysis (Section 6)
MIN_PROFESSION_SIZE = 200

# Headroom calculation factors (Section 5)
PENDING_APPROVAL_RATE = 0.8
OUTFLOW_CONFIDENCE_FACTOR = 0.75

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

NUMERIC_TO_ISO = {v: k for k, v in NATIONALITY_CODES.items()}


def load_caps() -> dict:
    """Load nationality caps."""
    filepath = REAL_DATA_DIR / '05_nationality_caps.csv'
    caps = {}
    with open(filepath, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            nat_code = row.get('nationality_code', '')
            if nat_code:
                caps[nat_code] = {
                    'current_cap': int(row.get('cap_limit', 0) or 0),
                    'previous_cap': int(row.get('previous_cap', 0) or 0),
                }
    return caps


def load_professions() -> dict:
    """Load profession reference data."""
    filepath = REAL_DATA_DIR / '02_professions.csv'
    profs = {}
    with open(filepath, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            profs[row['code']] = row.get('name_en', row.get('name', f'Code_{row["code"]}'))
    return profs


def load_nationalities() -> dict:
    """Load nationality reference data."""
    filepath = REAL_DATA_DIR / '01_nationalities.csv'
    nats = {}
    with open(filepath, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            nats[row['code']] = row.get('name_en', row.get('name', row['code']))
    return nats


def create_summary():
    """
    Create summary data from worker stock.
    
    Two-pass algorithm:
    1. First pass: Count workers by (nationality, profession) AND total by profession
    2. Second pass: Calculate tier shares and dominance shares correctly
    """
    print("Loading reference data...")
    caps = load_caps()
    professions = load_professions()
    nationalities = load_nationalities()
    
    print("Processing worker stock (this may take a few minutes)...")
    print("  Pass 1: Counting workers by nationality and profession...")
    
    # Initialize counters for all tracked nationalities
    summary = {}
    for iso_code, num_code in NATIONALITY_CODES.items():
        summary[iso_code] = {
            'numeric_code': num_code,
            'name': nationalities.get(num_code, iso_code),
            'in_country': 0,
            'out_country': 0,
            'committed': 0,
            'pending': 0,
            'profession_counts': defaultdict(int),  # Workers by profession for this nationality
            'cap': caps.get(num_code, {}).get('current_cap', 0),
            'previous_cap': caps.get(num_code, {}).get('previous_cap', 0),
        }
    
    # CRITICAL: Track total workers per profession across ALL nationalities
    # This is needed for correct Dominance calculation (Section 6)
    total_workers_by_profession = defaultdict(int)
    
    # Process worker stock file - PASS 1
    worker_file = REAL_DATA_DIR / '07_worker_stock.csv'
    row_count = 0
    matched_count = 0
    
    with open(worker_file, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_count += 1
            if row_count % 500000 == 0:
                print(f"    Processed {row_count:,} rows...")
            
            nat_code = row.get('nationality_code', '') or row.get('nationality', '')
            iso_code = NUMERIC_TO_ISO.get(nat_code)
            state = row.get('state', '').upper()
            prof_code = row.get('profession_code', 'Unknown')
            
            # Count ALL workers by profession (for dominance calculation)
            # Only count active/in-country workers
            if state in ('ACTIVE', 'IN_COUNTRY', ''):
                total_workers_by_profession[prof_code] += 1
            
            # Track nationality-specific data only for our 12 nationalities
            if not iso_code:
                continue
            
            matched_count += 1
            
            if state in ('ACTIVE', 'IN_COUNTRY', ''):
                summary[iso_code]['in_country'] += 1
                summary[iso_code]['profession_counts'][prof_code] += 1
            elif state == 'OUT_COUNTRY':
                summary[iso_code]['out_country'] += 1
            elif state == 'COMMITTED':
                summary[iso_code]['committed'] += 1
            elif state == 'PENDING':
                summary[iso_code]['pending'] += 1
    
    print(f"    Total rows: {row_count:,}")
    print(f"    Matched rows (12 nationalities): {matched_count:,}")
    print(f"    Total professions tracked: {len(total_workers_by_profession):,}")
    
    # PASS 2: Calculate derived values with CORRECT formulas
    print("  Pass 2: Calculating metrics with exact documentation formulas...")
    
    for iso_code, data in summary.items():
        stock = data['in_country']
        cap = data['cap']
        committed = data['committed']
        pending = data['pending']
        
        # ================================================================
        # HEADROOM CALCULATION (Section 5, Section 11.B)
        # Formula: cap - stock - committed - (pending × 0.8) + (outflow × 0.75)
        # ================================================================
        projected_outflow = int(stock * 0.015 * 3)  # ~1.5% monthly for 3 months
        
        if cap > 0:
            headroom = (cap 
                       - stock 
                       - committed 
                       - int(pending * PENDING_APPROVAL_RATE) 
                       + int(projected_outflow * OUTFLOW_CONFIDENCE_FACTOR))
            headroom = max(0, headroom)
            utilization = stock / cap
        else:
            headroom = 0
            utilization = 0
        
        data['projected_outflow'] = projected_outflow
        data['stock'] = stock
        data['headroom'] = headroom
        data['utilization'] = utilization
        
        # ================================================================
        # TIER CLASSIFICATION (Section 4, Section 11.A)
        # Formula: Share = Workers_in_Profession / Total_Workers_of_Nationality
        # This is DIFFERENT from dominance - this measures profession demand
        # ================================================================
        total_workers_this_nationality = sum(data['profession_counts'].values())
        
        tier_summary = {
            1: {'count': 0, 'workers': 0, 'profs': []},
            2: {'count': 0, 'workers': 0, 'profs': []},
            3: {'count': 0, 'workers': 0, 'profs': []},
            4: {'count': 0, 'workers': 0, 'profs': []},
        }
        
        for prof_code, count in sorted(data['profession_counts'].items(), key=lambda x: -x[1]):
            # Tier share = profession's share within THIS nationality
            tier_share = count / total_workers_this_nationality if total_workers_this_nationality > 0 else 0
            
            # Determine tier (Section 4 thresholds)
            if tier_share >= TIER_1_THRESHOLD:
                tier = 1
            elif tier_share >= TIER_2_THRESHOLD:
                tier = 2
            elif tier_share >= TIER_3_THRESHOLD:
                tier = 3
            else:
                tier = 4
            
            tier_summary[tier]['count'] += 1
            tier_summary[tier]['workers'] += count
            
            if len(tier_summary[tier]['profs']) < 10:
                tier_summary[tier]['profs'].append({
                    'code': prof_code,
                    'name': professions.get(prof_code, f'Code_{prof_code}'),
                    'count': count,
                    'share': round(tier_share, 4)
                })
        
        # Store tier data
        data['tier_summary'] = {}
        for tier_level in [1, 2, 3, 4]:
            ts = tier_summary[tier_level]
            tier_total_share = ts['workers'] / total_workers_this_nationality if total_workers_this_nationality > 0 else 0
            data['tier_summary'][tier_level] = {
                'profession_count': ts['count'],
                'worker_count': ts['workers'],
                'share': round(tier_total_share, 4),
                'top_professions': ts['profs'][:5]
            }
        
        # ================================================================
        # DOMINANCE ALERTS (Section 6, Section 11.D)
        # Formula: Dominance_Share = Nationality_Workers_in_Profession / Total_Workers_in_Profession
        # This is DIFFERENT from tier - this measures concentration risk
        # ================================================================
        dominance_alerts = []
        
        for prof_code, nat_workers_in_prof in data['profession_counts'].items():
            total_in_profession = total_workers_by_profession.get(prof_code, 0)
            
            # Skip professions with fewer than MIN_PROFESSION_SIZE workers (Section 6)
            if total_in_profession < MIN_PROFESSION_SIZE:
                continue
            
            # Calculate dominance share per documentation
            # Dominance = Nationality workers in profession / ALL workers in profession
            dominance_share = nat_workers_in_prof / total_in_profession if total_in_profession > 0 else 0
            
            # Check against dominance thresholds (Section 6)
            if dominance_share >= DOMINANCE_WATCH:
                if dominance_share >= DOMINANCE_CRITICAL:
                    level = "CRITICAL"
                    is_blocking = True
                elif dominance_share >= DOMINANCE_HIGH:
                    level = "HIGH"
                    is_blocking = False
                else:
                    level = "WATCH"
                    is_blocking = False
                
                dominance_alerts.append({
                    'profession_code': prof_code,
                    'profession_name': professions.get(prof_code, f'Code_{prof_code}'),
                    'share': round(dominance_share, 4),
                    'nationality_workers': nat_workers_in_prof,
                    'total_workers_in_profession': total_in_profession,
                    'alert_level': level,
                    'is_blocking': is_blocking
                })
        
        # Sort alerts by share descending
        dominance_alerts.sort(key=lambda x: -x['share'])
        data['dominance_alerts'] = dominance_alerts
        
        # Keep top professions for reference
        top_profs = sorted(data['profession_counts'].items(), key=lambda x: -x[1])[:20]
        data['top_professions'] = [
            {'code': code, 'name': professions.get(code, code), 'count': count}
            for code, count in top_profs
        ]
        del data['profession_counts']
    
    # Save summary
    print(f"Saving summary to {SUMMARY_FILE}...")
    output = {
        'generated_at': datetime.now().isoformat(),
        'formula_version': '2.0',
        'documentation_reference': 'System_Documentation.md',
        'nationalities': summary,
        'global_stats': {
            'total_professions': len(total_workers_by_profession),
            'professions_with_min_size': sum(1 for c in total_workers_by_profession.values() if c >= MIN_PROFESSION_SIZE),
            'min_profession_size_threshold': MIN_PROFESSION_SIZE,
        }
    }
    
    with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("Done!")
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY - Exact Documentation Formulas Applied")
    print("=" * 70)
    print(f"{'Code':<5} {'Stock':>10} {'Cap':>10} {'Util':>8} {'Headroom':>10} {'Alerts':>7}")
    print("-" * 70)
    for iso_code in sorted(summary.keys()):
        data = summary[iso_code]
        alerts = len(data['dominance_alerts'])
        alert_str = f"{alerts}" if alerts == 0 else f"{alerts} (!)"
        print(f"{iso_code:<5} {data['stock']:>10,} {data['cap']:>10,} "
              f"{data['utilization']:>7.1%} {data['headroom']:>10,} {alert_str:>7}")
    
    # Print dominance alerts detail
    print("\n" + "=" * 70)
    print("DOMINANCE ALERTS (Section 6 Formula Applied)")
    print("Formula: Dominance_Share = Nat_Workers / Total_Workers_in_Profession")
    print(f"Min Profession Size: {MIN_PROFESSION_SIZE}")
    print("=" * 70)
    
    for iso_code in sorted(summary.keys()):
        alerts = summary[iso_code]['dominance_alerts']
        if alerts:
            print(f"\n{iso_code} ({summary[iso_code]['name']}):")
            for a in alerts[:3]:  # Show top 3
                print(f"  [{a['alert_level']}] {a['profession_name']}: "
                      f"{a['share']:.1%} ({a['nationality_workers']:,}/{a['total_workers_in_profession']:,})")


if __name__ == '__main__':
    create_summary()
