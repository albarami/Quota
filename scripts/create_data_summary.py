#!/usr/bin/env python
"""
Create summary data files for faster Streamlit loading.

This script pre-computes summaries from the large worker_stock.csv file
to enable fast dashboard loading.
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
    """Create summary data from worker stock."""
    print("Loading reference data...")
    caps = load_caps()
    professions = load_professions()
    nationalities = load_nationalities()
    
    print("Processing worker stock (this may take a few minutes)...")
    
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
            'profession_counts': defaultdict(int),
            'cap': caps.get(num_code, {}).get('current_cap', 0),
            'previous_cap': caps.get(num_code, {}).get('previous_cap', 0),
        }
    
    # Process worker stock file
    worker_file = REAL_DATA_DIR / '07_worker_stock.csv'
    row_count = 0
    matched_count = 0
    
    with open(worker_file, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_count += 1
            if row_count % 500000 == 0:
                print(f"  Processed {row_count:,} rows...")
            
            nat_code = row.get('nationality_code', '') or row.get('nationality', '')
            iso_code = NUMERIC_TO_ISO.get(nat_code)
            
            if not iso_code:
                continue
            
            matched_count += 1
            state = row.get('state', '').upper()
            prof_code = row.get('profession_code', 'Unknown')
            
            if state in ('ACTIVE', 'IN_COUNTRY', ''):
                summary[iso_code]['in_country'] += 1
                summary[iso_code]['profession_counts'][prof_code] += 1
            elif state == 'OUT_COUNTRY':
                summary[iso_code]['out_country'] += 1
            elif state == 'COMMITTED':
                summary[iso_code]['committed'] += 1
            elif state == 'PENDING':
                summary[iso_code]['pending'] += 1
    
    print(f"  Total rows: {row_count:,}")
    print(f"  Matched rows: {matched_count:,}")
    
    # Calculate derived values
    print("Calculating derived metrics...")
    for iso_code, data in summary.items():
        stock = data['in_country']
        cap = data['cap']
        committed = data['committed']
        pending = data['pending']
        
        # Calculate headroom and utilization
        if cap > 0:
            headroom = max(0, cap - stock - committed - int(pending * 0.8))
            utilization = stock / cap
        else:
            headroom = 0
            utilization = 0
        
        data['stock'] = stock
        data['headroom'] = headroom
        data['utilization'] = utilization
        
        # Calculate tier distribution and alerts
        total_workers = sum(data['profession_counts'].values())
        tier_summary = {1: {'count': 0, 'workers': 0, 'profs': []},
                       2: {'count': 0, 'workers': 0, 'profs': []},
                       3: {'count': 0, 'workers': 0, 'profs': []},
                       4: {'count': 0, 'workers': 0, 'profs': []}}
        
        alerts = []
        
        for prof_code, count in sorted(data['profession_counts'].items(), key=lambda x: -x[1]):
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
            
            if len(tier_summary[tier]['profs']) < 10:
                tier_summary[tier]['profs'].append({
                    'code': prof_code,
                    'name': professions.get(prof_code, f'Code_{prof_code}'),
                    'count': count,
                    'share': round(share, 4)
                })
            
            # Check for dominance alerts
            if share >= 0.30:
                level = "CRITICAL" if share >= 0.50 else "HIGH" if share >= 0.40 else "WATCH"
                alerts.append({
                    'profession_code': prof_code,
                    'profession_name': professions.get(prof_code, f'Code_{prof_code}'),
                    'share': round(share, 4),
                    'alert_level': level,
                    'is_blocking': share >= 0.50
                })
        
        # Store tier data
        data['tier_summary'] = {}
        for tier_level in [1, 2, 3, 4]:
            ts = tier_summary[tier_level]
            tier_share = ts['workers'] / total_workers if total_workers > 0 else 0
            data['tier_summary'][tier_level] = {
                'profession_count': ts['count'],
                'worker_count': ts['workers'],
                'share': round(tier_share, 4),
                'top_professions': ts['profs'][:5]
            }
        
        data['dominance_alerts'] = alerts
        
        # Remove the large profession_counts dict (keep top 20 only)
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
        'nationalities': summary
    }
    
    with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("Done!")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for iso_code in sorted(summary.keys()):
        data = summary[iso_code]
        alerts = len(data['dominance_alerts'])
        print(f"{iso_code}: Stock={data['stock']:>8,} | Cap={data['cap']:>8,} | "
              f"Util={data['utilization']:>6.1%} | Alerts={alerts}")


if __name__ == '__main__':
    create_summary()
