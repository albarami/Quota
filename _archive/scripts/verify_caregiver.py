"""Verify Care Giver profession data."""
import csv
from collections import defaultdict
from datetime import datetime

MIN_EMPLOYMENT_DAYS = 365
today = datetime.now()

# Load profession names and find Care Giver code
prof_names = {}
caregiver_code = None
with open('real_data/02_professions.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        prof_names[row['code']] = row.get('name', row['code'])
        if 'care giver' in row.get('name', '').lower():
            caregiver_code = row['code']
            print(f"Found Care Giver: Code={row['code']}, Name={row.get('name')}")

# Load nationality names
nat_names = {}
with open('real_data/01_nationalities.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        nat_names[row['code']] = row.get('name', row['code'])

# Count Care Giver workers by nationality
caregiver_by_nat = defaultdict(int)
total_caregivers = 0

with open('real_data/07_worker_stock.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        state = row.get('state', '').upper()
        prof_code = row.get('profession_code', '')
        nat = row.get('nationality_code', '')
        
        # Only IN_COUNTRY
        if state not in ('ACTIVE', 'IN_COUNTRY', ''):
            continue
        
        # Only Care Giver profession
        if prof_code != caregiver_code:
            continue
        
        # Filter short-term (< 1 year)
        emp_start = row.get('employment_start', '')
        if emp_start:
            try:
                start = datetime.strptime(emp_start[:10], '%Y-%m-%d')
                if (today - start).days < MIN_EMPLOYMENT_DAYS:
                    continue
            except:
                pass
        
        total_caregivers += 1
        caregiver_by_nat[nat] += 1

print(f"\n{'='*60}")
print(f"CARE GIVER VERIFICATION")
print(f"{'='*60}")
print(f"\nTotal Care Givers in Qatar: {total_caregivers:,}")
print(f"\nBreakdown by nationality:")
print(f"{'-'*60}")

for nat, count in sorted(caregiver_by_nat.items(), key=lambda x: -x[1]):
    pct = count / total_caregivers * 100 if total_caregivers > 0 else 0
    nat_name = nat_names.get(nat, nat)
    print(f"  {nat_name[:30]:<30} {count:>6,} ({pct:>5.1f}%)")

# Specifically check Philippines (608)
phl_count = caregiver_by_nat.get('608', 0)
phl_pct = phl_count / total_caregivers * 100 if total_caregivers > 0 else 0
print(f"\n{'='*60}")
print(f"PHILIPPINES DOMINANCE IN CARE GIVER:")
print(f"  Filipino Care Givers: {phl_count:,}")
print(f"  Total Care Givers: {total_caregivers:,}")
print(f"  Dominance: {phl_pct:.1f}%")
print(f"{'='*60}")
