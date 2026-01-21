#!/usr/bin/env python
"""Test the real data loader."""

import sys
sys.path.insert(0, 'D:/Quota')

from app.utils.real_data_loader import get_real_dashboard_data, check_real_data_available

print('Real data available:', check_real_data_available())
print()

# Test all nationalities
test_codes = ['EGY', 'YEM', 'SYR', 'IRQ', 'AFG', 'IRN', 'BGD', 'PAK', 'IND', 'NPL', 'PHL', 'LKA']

for code in test_codes:
    data = get_real_dashboard_data(code)
    if data:
        stock = data['stock']
        cap = data['cap']
        util = data['utilization_pct']
        alerts = len(data['dominance_alerts'])
        print(f"{code}: Stock={stock:>8,} | Cap={cap:>8,} | Util={util:>6.1%} | Alerts={alerts}")
        
        if data['dominance_alerts']:
            for a in data['dominance_alerts'][:1]:
                print(f"       Alert: {a['profession_name']} at {a['share_pct']:.1%} ({a['alert_level']})")
    else:
        print(f"{code}: No data")
