#!/usr/bin/env python
"""Check Egyptian labourer percentages."""

import csv
from collections import defaultdict

# Load professions
prof_map = {}
with open('real_data/02_professions.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        code = row.get('code', '').strip()
        name = row.get('name', '').strip().upper()
        if code:
            prof_map[code] = name

# Count Egyptian workers by profession
egypt_profs = defaultdict(int)
egypt_total = 0

with open('real_data/07_worker_stock.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        nat_code = row.get('nationality_code', '').strip().strip('"')
        state = row.get('state', '').strip().upper()
        prof_code = row.get('profession_code', '').strip().strip('"')
        
        if nat_code == '818' and state == 'IN_COUNTRY':
            egypt_total += 1
            prof_name = prof_map.get(prof_code, prof_code)
            egypt_profs[prof_name] += 1

print(f'Total Egyptian workers in country: {egypt_total:,}')
print()
print('LABOURER-RELATED PROFESSIONS:')
print('-' * 60)

labourer_total = 0
for name, count in sorted(egypt_profs.items(), key=lambda x: x[1], reverse=True):
    if 'LABOUR' in name or 'LABOR' in name or 'WORKER' in name:
        pct = count / egypt_total * 100
        print(f'{name:<40} {count:>8,} ({pct:>5.2f}%)')
        labourer_total += count

print('-' * 60)
print(f'{"TOTAL LABOURERS/WORKERS":<40} {labourer_total:>8,} ({labourer_total/egypt_total*100:>5.2f}%)')
print()
print()
print('TOP 20 PROFESSIONS (ALL):')
print('-' * 60)
for i, (name, count) in enumerate(sorted(egypt_profs.items(), key=lambda x: x[1], reverse=True)[:20], 1):
    pct = count / egypt_total * 100
    print(f'{i:>2}. {name:<38} {count:>8,} ({pct:>5.2f}%)')
