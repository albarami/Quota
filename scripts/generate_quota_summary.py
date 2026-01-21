#!/usr/bin/env python
"""
Generate Quota Summary - Pre-compute all v4 metrics.

This script generates a comprehensive JSON summary of all quota metrics
using the quota_engine v4 methodology.

Usage:
    python scripts/generate_quota_summary.py

Output:
    real_data/quota_summary.json - Complete metrics for all nationalities
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.engines.quota_engine import (
    get_all_metrics,
    get_all_nationalities,
    is_qvc_country,
    is_outflow_based,
    get_qvc_capacity_details,
    QVC_COUNTRIES,
    OUTFLOW_BASED,
    STANDARD_NON_QVC,
    QVC_ANNUAL_CAPACITY,
    DATA_DIR,
    clear_cache,
)


def generate_summary() -> dict:
    """
    Generate comprehensive summary for all nationalities.
    
    Returns:
        Dictionary with all quota metrics
    """
    print("=" * 70)
    print("QUOTA SUMMARY GENERATOR v4")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Clear cache to ensure fresh data
    clear_cache()
    
    # Get all nationality codes
    all_codes = get_all_nationalities()
    
    print(f"\nProcessing {len(all_codes)} nationalities...")
    
    # Process each nationality
    nationalities = {}
    total_stock = 0
    total_recommended_cap = 0
    qvc_stock = 0
    qvc_cap = 0
    outflow_stock = 0
    outflow_cap = 0
    
    for code in all_codes:
        print(f"  Processing {code}...", end=" ")
        try:
            metrics = get_all_metrics(code)
            nationalities[code] = metrics
            
            # Update totals
            total_stock += metrics['current_stock']
            total_recommended_cap += metrics['recommended_cap']
            
            if code in QVC_COUNTRIES:
                qvc_stock += metrics['current_stock']
                qvc_cap += metrics['recommended_cap']
            elif code in OUTFLOW_BASED:
                outflow_stock += metrics['current_stock']
                outflow_cap += metrics['recommended_cap']
            
            print(f"Stock: {metrics['current_stock']:,}, Cap: {metrics['recommended_cap']:,}")
        except Exception as e:
            print(f"ERROR: {e}")
            nationalities[code] = {'error': str(e)}
    
    # Build QVC summary
    qvc_summary = {
        'countries': QVC_COUNTRIES,
        'total_daily_capacity': sum(QVC_ANNUAL_CAPACITY.values()) // 264,
        'total_annual_capacity': sum(QVC_ANNUAL_CAPACITY.values()),
        'total_stock': qvc_stock,
        'total_cap': qvc_cap,
        'centers': {},
    }
    
    for code in QVC_COUNTRIES:
        details = get_qvc_capacity_details(code)
        if details:
            qvc_summary['centers'][code] = details
    
    # Build outflow summary
    outflow_summary = {
        'countries': OUTFLOW_BASED,
        'total_stock': outflow_stock,
        'total_cap': outflow_cap,
        'monthly_allocations': {},
    }
    
    for code in OUTFLOW_BASED:
        if code in nationalities:
            metrics = nationalities[code]
            if isinstance(metrics, dict) and 'monthly_allocation' in metrics:
                outflow_summary['monthly_allocations'][code] = metrics.get('monthly_allocation', 0)
    
    # Build complete summary
    summary = {
        'generated_at': datetime.now().isoformat(),
        'formula_version': '4.0',
        'documentation_reference': 'Quota_Allocation_Methodology_v4.md',
        
        # Totals
        'totals': {
            'total_nationalities': len(all_codes),
            'total_stock': total_stock,
            'total_recommended_cap': total_recommended_cap,
            'total_headroom': total_recommended_cap - total_stock,
            'overall_utilization_pct': round(total_stock / total_recommended_cap * 100, 1) if total_recommended_cap > 0 else 0,
        },
        
        # Country Classification
        'classification': {
            'qvc_countries': QVC_COUNTRIES,
            'outflow_based_countries': OUTFLOW_BASED,
            'standard_non_qvc_countries': STANDARD_NON_QVC,
        },
        
        # QVC Summary
        'qvc_summary': qvc_summary,
        
        # Outflow Summary
        'outflow_summary': outflow_summary,
        
        # All Nationalities
        'nationalities': nationalities,
    }
    
    return summary


def print_report(summary: dict):
    """Print a summary report to console."""
    print("\n" + "=" * 70)
    print("SUMMARY REPORT")
    print("=" * 70)
    
    totals = summary['totals']
    print(f"\nTotal Stock: {totals['total_stock']:,}")
    print(f"Total Recommended Cap: {totals['total_recommended_cap']:,}")
    print(f"Total Headroom: {totals['total_headroom']:,}")
    print(f"Overall Utilization: {totals['overall_utilization_pct']:.1f}%")
    
    print("\n" + "-" * 70)
    print("QVC COUNTRIES")
    print("-" * 70)
    print(f"{'Code':<6} {'Stock':>12} {'Rec. Cap':>12} {'Headroom':>12} {'QVC Const':>10}")
    print("-" * 70)
    
    for code in QVC_COUNTRIES:
        if code in summary['nationalities']:
            m = summary['nationalities'][code]
            if isinstance(m, dict) and 'current_stock' in m:
                constrained = "YES" if m.get('is_qvc_constrained', False) else "No"
                print(f"{code:<6} {m['current_stock']:>12,} {m['recommended_cap']:>12,} {m['headroom']:>12,} {constrained:>10}")
    
    print("\n" + "-" * 70)
    print("OUTFLOW-BASED COUNTRIES")
    print("-" * 70)
    print(f"{'Code':<6} {'Stock':>12} {'Cap (Frozen)':>12} {'Monthly':>10}")
    print("-" * 70)
    
    for code in OUTFLOW_BASED:
        if code in summary['nationalities']:
            m = summary['nationalities'][code]
            if isinstance(m, dict) and 'current_stock' in m:
                monthly = m.get('monthly_allocation', 0) or 0
                print(f"{code:<6} {m['current_stock']:>12,} {m['recommended_cap']:>12,} {monthly:>10,}")
    
    print("\n" + "-" * 70)
    print("STANDARD NON-QVC")
    print("-" * 70)
    
    for code in STANDARD_NON_QVC:
        if code in summary['nationalities']:
            m = summary['nationalities'][code]
            if isinstance(m, dict) and 'current_stock' in m:
                print(f"{code}: Stock={m['current_stock']:,}, Cap={m['recommended_cap']:,}, Headroom={m['headroom']:,}")
    
    print("\n" + "=" * 70)


def main():
    """Main entry point."""
    # Generate summary
    summary = generate_summary()
    
    # Print report
    print_report(summary)
    
    # Save to JSON
    output_path = DATA_DIR / 'quota_summary.json'
    
    print(f"\nSaving to: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print("[OK] Summary saved successfully!")
    
    # Also update the summary_by_nationality.json for compatibility
    compat_path = DATA_DIR / 'summary_by_nationality.json'
    
    compat_summary = {
        'generated_at': summary['generated_at'],
        'formula_version': summary['formula_version'],
        'documentation_reference': summary['documentation_reference'],
        'nationalities': {},
    }
    
    for code, metrics in summary['nationalities'].items():
        if isinstance(metrics, dict) and 'current_stock' in metrics:
            compat_summary['nationalities'][code] = {
                'numeric_code': metrics.get('nationality_code', code),
                'name': metrics.get('nationality_name', code),
                'stock': metrics['current_stock'],
                'cap': metrics['recommended_cap'],
                'headroom': metrics['headroom'],
                'utilization': metrics['utilization_pct'] / 100,
                'growth_rate': metrics['growth_rate'],
                'country_type': metrics['country_type'],
                'is_qvc_constrained': metrics.get('is_qvc_constrained', False),
                'tier_summary': metrics.get('tier_summary', {}),
                'dominance_alerts': metrics.get('dominance_alerts', []),
            }
    
    print(f"Saving compatibility file to: {compat_path}")
    
    with open(compat_path, 'w', encoding='utf-8') as f:
        json.dump(compat_summary, f, indent=2, ensure_ascii=False)
    
    print("[OK] Compatibility summary saved!")
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
