#!/usr/bin/env python
"""Test that local data matches what Streamlit Cloud will see."""
import sys
sys.path.insert(0, 'D:/Quota')

from app.utils.real_data_loader import get_real_dashboard_data, check_real_data_available, SUMMARY_FILE

print("=" * 70)
print("LOCAL STREAMLIT DATA VERIFICATION")
print("=" * 70)
print(f"\nSummary file exists: {SUMMARY_FILE.exists()}")
print(f"Real data available: {check_real_data_available()}")
print()

# Test all 12 nationalities
codes = ['EGY', 'YEM', 'SYR', 'IRQ', 'AFG', 'IRN', 'BGD', 'IND', 'NPL', 'PAK', 'PHL', 'LKA']

print(f"{'Code':<6} {'Stock':>12} {'Cap':>12} {'Util':>8} {'Growth':>8} {'Alerts':>8} {'Source':<10}")
print("-" * 70)

total_workers = 0
for code in codes:
    data = get_real_dashboard_data(code)
    if data:
        stock = data['stock']
        cap = data['cap']
        util = data['utilization_pct']
        growth = data.get('growth_rate', 0)
        alerts = len(data.get('dominance_alerts', []))
        source = data.get('data_source', 'unknown')
        total_workers += stock
        print(f"{code:<6} {stock:>12,} {cap:>12,} {util*100:>7.1f}% {growth:>+7.1f}% {alerts:>8} {source:<10}")
    else:
        print(f"{code:<6} NO DATA")

print("-" * 70)
print(f"{'TOTAL':<6} {total_workers:>12,}")
print()
print("This is exactly what Streamlit Cloud will display.")
