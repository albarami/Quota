#!/usr/bin/env python
"""Check if Iran data exists."""

import csv
import sys
from collections import defaultdict

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Iran ISO code is 364
IRAN_CODE = '364'

# Check nationalities file
print("Checking nationalities file...")
with open('real_data/01_nationalities.csv', encoding='utf-8') as f:
    nats = list(csv.DictReader(f))
    
# Find Iran
iran_entry = None
for n in nats:
    code = n.get('code', '')
    name = n.get('name_en', '') or n.get('name', '')
    if code == IRAN_CODE or 'iran' in name.lower():
        iran_entry = n
        print(f"Found Iran: {n}")
        break

if not iran_entry:
    print(f"Iran (code {IRAN_CODE}) not found in nationalities file")
    print("\nAll nationality codes in file:")
    for n in nats:
        print(f"  {n.get('code', 'N/A')}: {n.get('name_en', n.get('name', 'N/A'))}")
else:
    # Check worker stock for Iran
    print("\nChecking worker stock for Iran...")
    with open('real_data/07_worker_stock.csv', encoding='utf-8') as f:
        workers = list(csv.DictReader(f))
    
    iran_workers = [w for w in workers if w.get('nationality_code') == IRAN_CODE or w.get('nationality') == IRAN_CODE]
    print(f"Iran workers found: {len(iran_workers)}")
    
    if iran_workers:
        # Count by profession
        prof_counts = defaultdict(int)
        for w in iran_workers:
            prof = w.get('profession_code', 'Unknown')
            prof_counts[prof] += 1
        
        print(f"\nTop professions for Iran:")
        for prof, count in sorted(prof_counts.items(), key=lambda x: -x[1])[:20]:
            print(f"  {prof}: {count}")
