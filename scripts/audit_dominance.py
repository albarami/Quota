#!/usr/bin/env python
"""
DOMINANCE AUDIT SCRIPT

Thoroughly checks ALL professions for dominance alerts.
Does NOT limit to top N professions - checks every single one.

Formula (Section 6): Dominance_Share = Nationality_Workers / Total_Workers_in_Profession
Thresholds: WATCH >= 30%, HIGH >= 40%, CRITICAL >= 50%
Minimum profession size: 200 workers
"""

import csv
from pathlib import Path
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
REAL_DATA_DIR = PROJECT_ROOT / 'real_data'

# Thresholds from System_Documentation.md Section 6
DOMINANCE_WATCH = 0.30
DOMINANCE_HIGH = 0.40
DOMINANCE_CRITICAL = 0.50
MIN_PROFESSION_SIZE = 200
MIN_EMPLOYMENT_DAYS = 365

# All 12 nationalities
NATIONALITY_CODES = {
    'EGY': '818', 'IND': '356', 'PAK': '586', 'NPL': '524',
    'BGD': '050', 'PHL': '608', 'IRN': '364', 'IRQ': '368',
    'YEM': '886', 'SYR': '760', 'AFG': '004', 'LKA': '144',
}
NUMERIC_TO_ISO = {v: k for k, v in NATIONALITY_CODES.items()}


def load_professions():
    """Load profession names."""
    filepath = REAL_DATA_DIR / '02_professions.csv'
    profs = {}
    with open(filepath, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            profs[row['code']] = row.get('name', row['code'])
    return profs


def load_nationalities():
    """Load nationality names."""
    filepath = REAL_DATA_DIR / '01_nationalities.csv'
    nats = {}
    with open(filepath, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            nats[row['code']] = row.get('name', row['code'])
    return nats


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


def audit_dominance():
    """
    Comprehensive dominance audit - checks EVERY profession.
    """
    print("=" * 100)
    print("DOMINANCE AUDIT - COMPREHENSIVE CHECK")
    print("=" * 100)
    print(f"Audit Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Formula: Dominance_Share = Nationality_Workers / Total_Workers_in_Profession")
    print(f"Min Profession Size: {MIN_PROFESSION_SIZE}")
    print(f"Thresholds: WATCH >= {DOMINANCE_WATCH*100:.0f}%, HIGH >= {DOMINANCE_HIGH*100:.0f}%, CRITICAL >= {DOMINANCE_CRITICAL*100:.0f}%")
    print()
    
    professions = load_professions()
    nationalities = load_nationalities()
    
    # Data structures
    # Key: profession_code -> {nationality_code: count}
    workers_by_prof_and_nat = defaultdict(lambda: defaultdict(int))
    # Key: profession_code -> total count
    total_by_profession = defaultdict(int)
    
    # Process worker file
    worker_file = REAL_DATA_DIR / '07_worker_stock.csv'
    today = datetime.now()
    
    print("Processing worker data (checking every profession)...")
    row_count = 0
    
    with open(worker_file, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_count += 1
            if row_count % 1000000 == 0:
                print(f"  Processed {row_count:,} rows...")
            
            state = row.get('state', '').upper()
            
            # Only count IN_COUNTRY workers
            if state not in ('ACTIVE', 'IN_COUNTRY', ''):
                continue
            
            # Skip short-term
            emp_start = row.get('employment_start', '')
            emp_end = row.get('employment_end', '')
            if not is_long_term(emp_start, emp_end, state, today):
                continue
            
            nat_code = row.get('nationality_code', '')
            prof_code = row.get('profession_code', 'Unknown')
            
            # Track total for this profession
            total_by_profession[prof_code] += 1
            
            # Track by nationality (only our 12)
            iso_code = NUMERIC_TO_ISO.get(nat_code)
            if iso_code:
                workers_by_prof_and_nat[prof_code][iso_code] += 1
    
    print(f"  Total rows processed: {row_count:,}")
    print(f"  Total unique professions: {len(total_by_profession):,}")
    print()
    
    # Now audit EVERY profession for dominance
    print("Auditing ALL professions for dominance...")
    print()
    
    all_alerts = []
    professions_checked = 0
    professions_skipped = 0
    
    for prof_code, total_workers in total_by_profession.items():
        if total_workers < MIN_PROFESSION_SIZE:
            professions_skipped += 1
            continue
        
        professions_checked += 1
        
        # Check each nationality's share in this profession
        for iso_code, nat_count in workers_by_prof_and_nat[prof_code].items():
            dominance_share = nat_count / total_workers
            
            if dominance_share >= DOMINANCE_WATCH:
                level = 'CRITICAL' if dominance_share >= DOMINANCE_CRITICAL else \
                        'HIGH' if dominance_share >= DOMINANCE_HIGH else 'WATCH'
                
                nat_num = NATIONALITY_CODES[iso_code]
                nat_name = nationalities.get(nat_num, iso_code)
                prof_name = professions.get(prof_code, prof_code)
                
                all_alerts.append({
                    'nationality': iso_code,
                    'nationality_name': nat_name,
                    'profession_code': prof_code,
                    'profession_name': prof_name,
                    'level': level,
                    'share': dominance_share,
                    'nat_workers': nat_count,
                    'total_workers': total_workers,
                })
    
    print(f"Professions checked (>= {MIN_PROFESSION_SIZE} workers): {professions_checked:,}")
    print(f"Professions skipped (< {MIN_PROFESSION_SIZE} workers): {professions_skipped:,}")
    print()
    
    # Sort alerts by share descending
    all_alerts.sort(key=lambda x: -x['share'])
    
    # Count by level
    critical = [a for a in all_alerts if a['level'] == 'CRITICAL']
    high = [a for a in all_alerts if a['level'] == 'HIGH']
    watch = [a for a in all_alerts if a['level'] == 'WATCH']
    
    print("=" * 100)
    print("AUDIT RESULTS")
    print("=" * 100)
    print(f"Total Dominance Alerts Found: {len(all_alerts)}")
    print(f"  CRITICAL (>= 50%): {len(critical)}")
    print(f"  HIGH (40-49%): {len(high)}")
    print(f"  WATCH (30-39%): {len(watch)}")
    print()
    
    # Group by nationality
    alerts_by_nat = defaultdict(list)
    for alert in all_alerts:
        alerts_by_nat[alert['nationality']].append(alert)
    
    print("-" * 100)
    print("ALERTS BY NATIONALITY")
    print("-" * 100)
    
    for iso_code in sorted(alerts_by_nat.keys(), key=lambda x: -len(alerts_by_nat[x])):
        alerts = alerts_by_nat[iso_code]
        nat_name = alerts[0]['nationality_name']
        critical_count = len([a for a in alerts if a['level'] == 'CRITICAL'])
        high_count = len([a for a in alerts if a['level'] == 'HIGH'])
        watch_count = len([a for a in alerts if a['level'] == 'WATCH'])
        
        print(f"\n{nat_name} ({iso_code}): {len(alerts)} alerts "
              f"(CRITICAL: {critical_count}, HIGH: {high_count}, WATCH: {watch_count})")
        print("-" * 80)
        
        for alert in sorted(alerts, key=lambda x: -x['share']):
            print(f"  [{alert['level']:>8}] {alert['profession_name'][:45]:<45} "
                  f"{alert['share']*100:>5.1f}% ({alert['nat_workers']:,}/{alert['total_workers']:,})")
    
    # Print TOP 20 CRITICAL alerts across all nationalities
    print("\n" + "=" * 100)
    print("TOP 20 CRITICAL ALERTS (ALL NATIONALITIES)")
    print("=" * 100)
    
    for i, alert in enumerate(critical[:20], 1):
        print(f"{i:>2}. [{alert['nationality']}] {alert['profession_name'][:40]:<40} "
              f"{alert['share']*100:>5.1f}% ({alert['nat_workers']:,}/{alert['total_workers']:,})")
    
    # Check for any professions dominated by multiple nationalities (combined > 80%)
    print("\n" + "=" * 100)
    print("PROFESSIONS WITH COMBINED DOMINANCE > 80%")
    print("(Multiple nationalities together control > 80% of profession)")
    print("=" * 100)
    
    for prof_code, total_workers in total_by_profession.items():
        if total_workers < MIN_PROFESSION_SIZE:
            continue
        
        # Sum all 12 nationalities' share
        combined_share = sum(workers_by_prof_and_nat[prof_code].values()) / total_workers
        
        if combined_share > 0.80:
            prof_name = professions.get(prof_code, prof_code)
            print(f"\n{prof_name} (Total: {total_workers:,}) - Combined: {combined_share*100:.1f}%")
            
            for iso_code, count in sorted(workers_by_prof_and_nat[prof_code].items(), 
                                          key=lambda x: -x[1]):
                if count > 0:
                    share = count / total_workers
                    print(f"  {iso_code}: {share*100:>5.1f}% ({count:,})")
    
    print("\n" + "=" * 100)
    print("AUDIT COMPLETE")
    print("=" * 100)
    
    return all_alerts


if __name__ == '__main__':
    audit_dominance()
