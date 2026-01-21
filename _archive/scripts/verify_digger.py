"""Verify DIGGER profession data."""
import csv
from collections import defaultdict
from datetime import datetime

# Find DIGGER profession code
print("Finding DIGGER profession codes:")
digger_codes = []
with open('real_data/02_professions.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        name = row.get('name', '').upper()
        if 'DIGGER' in name:
            print(f"  Code: {row['code']}, Name: {row.get('name', '')}")
            digger_codes.append(row['code'])

print(f"\nDigger codes found: {digger_codes}")

# Count workers by profession name containing DIGGER
print("\n\nCounting all professions with DIGGER in name:")
MIN_EMPLOYMENT_DAYS = 365
today = datetime.now()

# Load profession names
prof_names = {}
with open('real_data/02_professions.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        prof_names[row['code']] = row.get('name', row['code'])

# Count workers
workers_by_prof = defaultdict(lambda: defaultdict(int))
total_by_prof = defaultdict(int)

with open('real_data/07_worker_stock.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        state = row.get('state', '').upper()
        prof_code = row.get('profession_code', '')
        nat = row.get('nationality_code', '')
        
        if state not in ('ACTIVE', 'IN_COUNTRY', ''):
            continue
        
        # Filter short-term
        emp_start = row.get('employment_start', '')
        if emp_start:
            try:
                start = datetime.strptime(emp_start[:10], '%Y-%m-%d')
                if (today - start).days < MIN_EMPLOYMENT_DAYS:
                    continue
            except:
                pass
        
        prof_name = prof_names.get(prof_code, prof_code)
        
        total_by_prof[prof_code] += 1
        workers_by_prof[prof_code][nat] += 1

# Find professions where India (356) has high dominance
print("\n\nProfessions where India has >= 70% dominance:")
india_code = '356'

for prof_code, nat_counts in workers_by_prof.items():
    total = total_by_prof[prof_code]
    if total < 200:  # Min profession size
        continue
    
    india_count = nat_counts.get(india_code, 0)
    dominance = india_count / total if total > 0 else 0
    
    if dominance >= 0.70:
        prof_name = prof_names.get(prof_code, prof_code)
        print(f"  {prof_name}: {dominance:.1%} ({india_count:,}/{total:,})")
