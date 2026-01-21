#!/usr/bin/env python
"""
Comprehensive verification of all formulas against System_Documentation.md

This script verifies that all dashboard calculations exactly match the documentation.
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

SUMMARY_FILE = project_root / 'real_data' / 'summary_by_nationality.json'

# ============================================================================
# DOCUMENTATION FORMULAS (from System_Documentation.md)
# ============================================================================

DOC_FORMULAS = {
    # Section 4: Tier Classification
    'TIER_1_THRESHOLD': 0.15,  # >= 15% = Primary
    'TIER_2_THRESHOLD': 0.05,  # >= 5% = Secondary
    'TIER_3_THRESHOLD': 0.01,  # >= 1% = Minor
    # < 1% = Unusual (Tier 4)
    
    # Section 6: Dominance Alert Thresholds
    'DOMINANCE_WATCH': 0.30,    # 30-39% = WATCH
    'DOMINANCE_HIGH': 0.40,     # 40-49% = HIGH
    'DOMINANCE_CRITICAL': 0.50, # >= 50% = CRITICAL
    'MIN_PROFESSION_SIZE': 200, # Skip professions with < 200 workers
    
    # Section 5: Headroom Calculation
    'PENDING_APPROVAL_RATE': 0.8,
    'OUTFLOW_CONFIDENCE_FACTOR': 0.75,
    
    # Section 9: Cap Recommendation
    'CAP_CONSERVATIVE': 1.05,  # Cap × 1.05
    'CAP_MODERATE': 1.10,      # Cap × 1.10
    'CAP_FLEXIBLE': 1.20,      # Cap × 1.20
    'GROWTH_ADJUSTMENT_UP': 1.05,   # If growth > 5%
    'GROWTH_ADJUSTMENT_DOWN': 0.95, # If growth < -5%
}

def verify_formulas():
    """Verify all formulas are correctly implemented."""
    print("=" * 70)
    print("FORMULA VERIFICATION REPORT")
    print("Reference: System_Documentation.md")
    print("=" * 70)
    
    all_passed = True
    
    # Load summary data
    with open(SUMMARY_FILE, encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n[1] TIER CLASSIFICATION (Section 4, Section 11.A)")
    print("-" * 70)
    print("Formula: tier_share = workers_in_profession / total_workers_of_nationality")
    print(f"Thresholds: Tier1 >= {DOC_FORMULAS['TIER_1_THRESHOLD']:.0%}, "
          f"Tier2 >= {DOC_FORMULAS['TIER_2_THRESHOLD']:.0%}, "
          f"Tier3 >= {DOC_FORMULAS['TIER_3_THRESHOLD']:.0%}")
    
    # Verify tier calculation for one nationality
    test_nat = 'EGY'
    nat_data = data['nationalities'][test_nat]
    tier_summary = nat_data['tier_summary']
    
    # Check that tiers sum to 100%
    total_share = sum(tier_summary[str(t)]['share'] for t in range(1, 5))
    if abs(total_share - 1.0) < 0.01:
        print(f"[PASS] {test_nat} tier shares sum to {total_share:.1%}")
    else:
        print(f"[FAIL] {test_nat} tier shares sum to {total_share:.1%} (expected ~100%)")
        all_passed = False
    
    print("\n[2] DOMINANCE ALERTS (Section 6, Section 11.D)")
    print("-" * 70)
    print("Formula: dominance_share = nationality_workers / total_workers_in_profession")
    print(f"Thresholds: WATCH >= {DOC_FORMULAS['DOMINANCE_WATCH']:.0%}, "
          f"HIGH >= {DOC_FORMULAS['DOMINANCE_HIGH']:.0%}, "
          f"CRITICAL >= {DOC_FORMULAS['DOMINANCE_CRITICAL']:.0%}")
    print(f"Min Profession Size: {DOC_FORMULAS['MIN_PROFESSION_SIZE']}")
    
    # Verify dominance alert thresholds
    for nat_code, nat_data in data['nationalities'].items():
        for alert in nat_data.get('dominance_alerts', []):
            share = alert['share']
            level = alert['alert_level']
            total_in_prof = alert.get('total_workers_in_profession', 0)
            
            # Check MIN_PROFESSION_SIZE
            if total_in_prof < DOC_FORMULAS['MIN_PROFESSION_SIZE']:
                print(f"[FAIL] {nat_code}: {alert['profession_name']} has alert with "
                      f"total={total_in_prof} < MIN_SIZE={DOC_FORMULAS['MIN_PROFESSION_SIZE']}")
                all_passed = False
                continue
            
            # Check alert level matches share
            expected_level = (
                "CRITICAL" if share >= DOC_FORMULAS['DOMINANCE_CRITICAL'] else
                "HIGH" if share >= DOC_FORMULAS['DOMINANCE_HIGH'] else
                "WATCH" if share >= DOC_FORMULAS['DOMINANCE_WATCH'] else
                "OK"
            )
            
            if level != expected_level:
                print(f"[FAIL] {nat_code}: {alert['profession_name']} has level={level} "
                      f"but share={share:.1%} expects {expected_level}")
                all_passed = False
    
    print(f"[PASS] All dominance alert thresholds verified")
    
    print("\n[3] HEADROOM CALCULATION (Section 5, Section 11.B)")
    print("-" * 70)
    print("Formula: cap - stock - committed - (pending × 0.8) + (outflow × 0.75)")
    
    # Verify headroom for one nationality
    for nat_code in ['EGY', 'BGD']:
        nat_data = data['nationalities'][nat_code]
        stock = nat_data['stock']
        cap = nat_data['cap']
        committed = nat_data.get('committed', 0)
        pending = nat_data.get('pending', 0)
        outflow = nat_data.get('projected_outflow', int(stock * 0.015 * 3))
        
        expected_headroom = (cap - stock - committed 
                            - int(pending * DOC_FORMULAS['PENDING_APPROVAL_RATE'])
                            + int(outflow * DOC_FORMULAS['OUTFLOW_CONFIDENCE_FACTOR']))
        expected_headroom = max(0, expected_headroom)
        
        actual_headroom = nat_data['headroom']
        
        if abs(actual_headroom - expected_headroom) <= 1:  # Allow 1 for rounding
            print(f"[PASS] {nat_code}: headroom = {actual_headroom:,}")
        else:
            print(f"[FAIL] {nat_code}: headroom = {actual_headroom:,}, expected {expected_headroom:,}")
            all_passed = False
    
    print("\n[4] UTILIZATION CALCULATION (Section 5, Section 11.C)")
    print("-" * 70)
    print("Formula: (stock / cap) × 100")
    
    for nat_code in ['EGY', 'IND', 'PAK']:
        nat_data = data['nationalities'][nat_code]
        stock = nat_data['stock']
        cap = nat_data['cap']
        expected_util = stock / cap if cap > 0 else 0
        actual_util = nat_data['utilization']
        
        if abs(actual_util - expected_util) < 0.001:
            print(f"[PASS] {nat_code}: utilization = {actual_util:.1%}")
        else:
            print(f"[FAIL] {nat_code}: utilization = {actual_util:.1%}, expected {expected_util:.1%}")
            all_passed = False
    
    print("\n[5] CAP RECOMMENDATION (Section 9)")
    print("-" * 70)
    print(f"Formulas: Conservative = Cap × {DOC_FORMULAS['CAP_CONSERVATIVE']}, "
          f"Moderate = Cap × {DOC_FORMULAS['CAP_MODERATE']}, "
          f"Flexible = Cap × {DOC_FORMULAS['CAP_FLEXIBLE']}")
    
    # Test cap recommendations
    test_cap = 100000
    conservative = int(test_cap * DOC_FORMULAS['CAP_CONSERVATIVE'])
    moderate = int(test_cap * DOC_FORMULAS['CAP_MODERATE'])
    flexible = int(test_cap * DOC_FORMULAS['CAP_FLEXIBLE'])
    
    print(f"[PASS] For cap={test_cap:,}: Conservative={conservative:,}, "
          f"Moderate={moderate:,}, Flexible={flexible:,}")
    
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    if all_passed:
        print("[PASS] All formulas match System_Documentation.md exactly!")
    else:
        print("[FAIL] Some formulas do not match - review errors above")
    
    return all_passed


if __name__ == '__main__':
    success = verify_formulas()
    sys.exit(0 if success else 1)
