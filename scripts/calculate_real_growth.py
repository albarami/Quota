#!/usr/bin/env python
"""
Calculate ACTUAL growth rates from worker movement data.

Formula:
  Stock_end_2024 = Current_Stock + Left_2025 - Joined_2025
  Growth_Rate = (Current_Stock - Stock_end_2024) / Stock_end_2024 × 100
             = (Joined_2025 - Left_2025) / Stock_end_2024 × 100
"""

# Data from worker_stock.csv analysis
data = {
    #     Current,    Join2025,  Left2025
    'AFG': (2532,       242,       507),
    'BGD': (400273,     73661,     70012),
    'EGY': (71574,      42,        8703),
    'IND': (529575,     44734,     116602),
    'IRN': (6683,       263,       750),
    'IRQ': (1658,       81,        194),
    'LKA': (101272,     9097,      30414),
    'NPL': (346515,     31731,     66711),
    'PAK': (196277,     41436,     39993),
    'PHL': (126653,     6998,      26488),
    'SYR': (23324,      124,       3415),
    'YEM': (13105,      681,       848),
}

NAMES = {
    'AFG': 'Afghanistan',
    'BGD': 'Bangladesh',
    'EGY': 'Egypt',
    'IND': 'India',
    'IRN': 'Iran',
    'IRQ': 'Iraq',
    'LKA': 'Sri Lanka',
    'NPL': 'Nepal',
    'PAK': 'Pakistan',
    'PHL': 'Philippines',
    'SYR': 'Syria',
    'YEM': 'Yemen',
}

print("=" * 90)
print("ACTUAL GROWTH RATES CALCULATED FROM REAL DATA")
print("=" * 90)
print()
print(f"{'Country':<15} {'Current':>12} {'Est. End 2024':>14} {'Net Change':>12} {'Growth Rate':>12}")
print("-" * 90)

results = []
for iso in sorted(data.keys()):
    current, joined_2025, left_2025 = data[iso]
    
    # Estimate end of 2024 stock
    # Current = End2024 - Left2025 + Joined2025
    # End2024 = Current + Left2025 - Joined2025
    end_2024 = current + left_2025 - joined_2025
    
    # Net change in 2025
    net_change = joined_2025 - left_2025  # = Current - End2024
    
    # Growth rate
    if end_2024 > 0:
        growth_rate = (net_change / end_2024) * 100
    else:
        growth_rate = 0
    
    results.append((iso, current, end_2024, net_change, growth_rate))
    
    trend = "GROWING" if growth_rate > 0 else "SHRINKING" if growth_rate < 0 else "STABLE"
    print(f"{NAMES[iso]:<15} {current:>12,} {end_2024:>14,} {net_change:>+12,} {growth_rate:>+11.2f}%  ({trend})")

print("-" * 90)
print()
print("SUMMARY:")
print()

growing = [r for r in results if r[4] > 0]
shrinking = [r for r in results if r[4] < 0]

print("GROWING nationalities:")
for iso, _, _, net, rate in sorted(growing, key=lambda x: -x[4]):
    print(f"  {NAMES[iso]}: {rate:+.2f}% ({net:+,} workers)")

print()
print("SHRINKING nationalities:")
for iso, _, _, net, rate in sorted(shrinking, key=lambda x: x[4]):
    print(f"  {NAMES[iso]}: {rate:+.2f}% ({net:+,} workers)")

print()
print("=" * 90)
print("These are the CORRECT growth rates to use in the system.")
print("=" * 90)
