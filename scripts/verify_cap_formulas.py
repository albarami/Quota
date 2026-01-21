#!/usr/bin/env python
"""
Verify Cap Recommendation formulas match System_Documentation.md Section 9.

Formula Reference:
- Conservative: Current_Cap × 1.05
- Moderate: Current_Cap × 1.10
- Flexible: Current_Cap × 1.20

Selection Logic:
IF dominance_alerts > 3 OR has_critical_alert:
    recommendation = CONSERVATIVE
ELIF utilization > 90% OR dominance_alerts > 1:
    recommendation = MODERATE
ELIF utilization < 80% AND dominance_alerts == 0:
    recommendation = FLEXIBLE
ELSE:
    recommendation = MODERATE

Growth Adjustment:
IF growth_rate > 5%: recommended_cap × 1.05
IF growth_rate < -5%: recommended_cap × 0.95
"""

import sys
sys.path.insert(0, 'D:/Quota')

from app.utils.real_data_loader import get_real_dashboard_data

print("=" * 70)
print("CAP RECOMMENDATION FORMULA VERIFICATION")
print("Based on System_Documentation.md Section 9")
print("=" * 70)

# Growth rates from documentation
GROWTH_RATES = {
    'EGY': -4.55,   # Not < -5%, no adjustment
    'YEM': -1.62,   # Not < -5%, no adjustment  
    'SYR': -5.65,   # < -5%, triggers 5% reduction
    'AFG': +1.03,   # Not > 5%, no adjustment
}

test_cases = [
    {
        'code': 'EGY',
        'name': 'Egypt',
        'expected_level': 'moderate',  # 87.6% util (80-90%), 0 alerts
        'note': 'Utilization 87.6% is between 80-90%, falls to ELSE->MODERATE'
    },
    {
        'code': 'YEM', 
        'name': 'Yemen',
        'expected_level': 'conservative',  # Has CRITICAL alert
        'note': 'Has CRITICAL dominance alert (EMPLOYEE 51.4%)'
    },
    {
        'code': 'SYR',
        'name': 'Syria', 
        'expected_level': 'moderate',  # 86.3% util, 0 alerts, growth -5.65% triggers reduction
        'note': '86.3% util, but growth < -5% triggers 5% cap reduction'
    },
]

for tc in test_cases:
    code = tc['code']
    print(f"\n{'='*70}")
    print(f"TESTING: {code} - {tc['name']}")
    print(f"Expected Level: {tc['expected_level'].upper()}")
    print(f"Note: {tc['note']}")
    print("=" * 70)
    
    data = get_real_dashboard_data(code)
    if not data:
        print(f"  ERROR: No data for {code}")
        continue
    
    stock = data['stock']
    cap = data['cap']
    utilization_pct = (stock / cap * 100) if cap > 0 else 0
    alerts = len(data.get('dominance_alerts', []))
    has_critical = any(a.get('alert_level') == 'CRITICAL' for a in data.get('dominance_alerts', []))
    growth_rate = GROWTH_RATES.get(code, 0)
    
    print(f"\nInput Values:")
    print(f"  Stock: {stock:,}")
    print(f"  Cap: {cap:,}")
    print(f"  Utilization: {utilization_pct:.1f}%")
    print(f"  Alerts: {alerts}")
    print(f"  Has Critical: {has_critical}")
    print(f"  Growth Rate: {growth_rate:+.1f}%")
    
    # Calculate per documentation
    conservative = int(cap * 1.05)
    moderate = int(cap * 1.10)
    flexible = int(cap * 1.20)
    
    print(f"\nBase Calculations (Section 9):")
    print(f"  Conservative: {cap:,} × 1.05 = {conservative:,}")
    print(f"  Moderate: {cap:,} × 1.10 = {moderate:,}")
    print(f"  Flexible: {cap:,} × 1.20 = {flexible:,}")
    
    # Selection logic
    print(f"\nSelection Logic:")
    if alerts > 3 or has_critical:
        level = "conservative"
        recommended = conservative
        print(f"  IF alerts > 3 OR has_critical: TRUE -> CONSERVATIVE")
    elif utilization_pct > 90 or alerts > 1:
        level = "moderate"
        recommended = moderate
        print(f"  ELIF utilization > 90% OR alerts > 1: TRUE -> MODERATE")
    elif utilization_pct < 80 and alerts == 0:
        level = "flexible"
        recommended = flexible
        print(f"  ELIF utilization < 80% AND alerts == 0: TRUE -> FLEXIBLE")
    else:
        level = "moderate"
        recommended = moderate
        print(f"  ELSE: -> MODERATE")
    
    # Growth adjustment
    print(f"\nGrowth Adjustment:")
    if growth_rate > 5:
        recommended = int(recommended * 1.05)
        print(f"  growth_rate > 5%: {recommended // 1.05:,.0f} × 1.05 = {recommended:,}")
    elif growth_rate < -5:
        recommended = int(recommended * 0.95)
        print(f"  growth_rate < -5%: {recommended // 0.95:,.0f} × 0.95 = {recommended:,}")
    else:
        print(f"  No adjustment (growth_rate {growth_rate:+.1f}% is between -5% and +5%)")
    
    print(f"\nFinal Result:")
    print(f"  Level: {level.upper()}")
    print(f"  Recommended Cap: {recommended:,}")
    
    # Verify
    if level == tc['expected_level']:
        print(f"  [PASS] Level matches expected")
    else:
        print(f"  [FAIL] Expected {tc['expected_level'].upper()}, got {level.upper()}")

print("\n" + "=" * 70)
print("FORMULA REFERENCE (System_Documentation.md Section 9)")
print("=" * 70)
print("""
Conservative: Cap × 1.05 (High risk, many alerts)
Moderate: Cap × 1.10 (Balanced growth)  
Flexible: Cap × 1.20 (Low risk, high demand)

Selection Logic:
1. IF alerts > 3 OR critical_alert -> CONSERVATIVE
2. ELIF utilization > 90% OR alerts > 1 -> MODERATE
3. ELIF utilization < 80% AND alerts == 0 -> FLEXIBLE
4. ELSE -> MODERATE

Growth Adjustment:
- growth > +5% -> ×1.05
- growth < -5% -> ×0.95
""")
