#!/usr/bin/env python
"""
Calculate actual growth rates from worker stock data.

Growth Rate Formula (Section 10.G):
growth_rate = (net_change / previous_stock) × 100

We need to determine actual YoY changes.
"""
import csv
from collections import defaultdict
from datetime import datetime

# Nationality code mapping
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

print("=" * 80)
print("ANALYZING WORKER STOCK DATA FOR GROWTH RATES")
print("=" * 80)

# Count workers by nationality and employment year
workers_by_year = defaultdict(lambda: defaultdict(int))
current_stock = defaultdict(int)
workers_joined_2024 = defaultdict(int)
workers_joined_2025 = defaultdict(int)
workers_left_2024 = defaultdict(int)
workers_left_2025 = defaultdict(int)

print("\nReading worker_stock.csv (this may take a moment)...")

with open('real_data/07_worker_stock.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    row_count = 0
    for row in reader:
        row_count += 1
        nat_code = row.get('nationality_code', '')
        iso = NUMERIC_TO_ISO.get(nat_code)
        if not iso:
            continue
        
        state = row.get('state', '').upper()
        
        # Current stock (IN_COUNTRY)
        if state in ('IN_COUNTRY', 'ACTIVE', ''):
            current_stock[iso] += 1
        
        # Parse employment dates
        emp_start = row.get('employment_start', '')
        emp_end = row.get('employment_end', '')
        
        try:
            if emp_start:
                start_year = int(emp_start[:4])
                if start_year == 2024:
                    workers_joined_2024[iso] += 1
                elif start_year == 2025:
                    workers_joined_2025[iso] += 1
        except:
            pass
        
        try:
            if emp_end:
                end_year = int(emp_end[:4])
                if end_year == 2024:
                    workers_left_2024[iso] += 1
                elif end_year == 2025:
                    workers_left_2025[iso] += 1
        except:
            pass

print(f"Processed {row_count:,} rows")
print()

# Calculate growth analysis
print("=" * 80)
print(f"{'Country':<15} {'Current':>12} {'Join 2024':>12} {'Left 2024':>12} {'Join 2025':>12} {'Left 2025':>12}")
print("=" * 80)

for iso in sorted(NATIONALITY_CODES.keys()):
    curr = current_stock.get(iso, 0)
    j24 = workers_joined_2024.get(iso, 0)
    l24 = workers_left_2024.get(iso, 0)
    j25 = workers_joined_2025.get(iso, 0)
    l25 = workers_left_2025.get(iso, 0)
    print(f"{iso:<15} {curr:>12,} {j24:>12,} {l24:>12,} {j25:>12,} {l25:>12,}")

print("=" * 80)
print()
print("NOTE: To calculate actual growth rate, we need:")
print("  - Total stock as of Dec 31, 2024")
print("  - Total stock as of Dec 31, 2025 (or current)")
print()
print("If you have the 2024 totals, please provide them.")
