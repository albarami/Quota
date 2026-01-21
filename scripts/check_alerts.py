#!/usr/bin/env python
"""Check alerts in summary file."""
import json

with open('real_data/summary_by_nationality.json') as f:
    data = json.load(f)

nats = data['nationalities']
print("Alerts by nationality:")
print("=" * 50)
for code in sorted(nats.keys()):
    alerts = nats[code].get('dominance_alerts', [])
    print(f"{code}: {len(alerts)} alerts")
    for a in alerts:
        print(f"    - {a['profession_name']}: {a['share']*100:.1f}% ({a['alert_level']})")
