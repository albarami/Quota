#!/usr/bin/env python
"""Verify summary file has all 12 nationalities with correct data."""

import json
from pathlib import Path

summary_file = Path('real_data/summary_by_nationality.json')
data = json.load(open(summary_file, encoding='utf-8'))

nats = data['nationalities']
print(f"Generated at: {data['generated_at']}")
print(f"Total nationalities: {len(nats)}")
print()
print("=" * 80)
print(f"{'Code':<6} {'Name':<20} {'Stock':>12} {'Cap':>12} {'Util':>8} {'Alerts':>8}")
print("=" * 80)

for code in sorted(nats.keys()):
    n = nats[code]
    print(f"{code:<6} {n['name'][:20]:<20} {n['stock']:>12,} {n['cap']:>12,} {n['utilization']*100:>7.1f}% {len(n['dominance_alerts']):>8}")

print("=" * 80)
print(f"Total workers: {sum(n['stock'] for n in nats.values()):,}")
