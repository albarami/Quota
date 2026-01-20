#!/usr/bin/env python
"""
QVC Countries Tier Analysis Report.

Analyzes VP (Visa Permit) data for countries with QVC offices:
- Bangladesh, India, Nepal, Pakistan, Philippines, Sri Lanka

Generates tier classification reports based on profession distribution.
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Paths
DATA_FILE = Path('data/VP_2025_QVC.xlsx')
REPORT_DIR = Path('reports')


def calculate_tier(share_pct: float) -> tuple:
    """Calculate tier level based on share percentage."""
    if share_pct >= 0.15:
        return 1, "Primary", ">15%"
    elif share_pct >= 0.05:
        return 2, "Secondary", "5-15%"
    elif share_pct >= 0.01:
        return 3, "Minor", "1-5%"
    else:
        return 4, "Unusual", "<1%"


def analyze_qvc_data():
    """Analyze QVC VP data and generate reports."""
    print("=" * 80)
    print("QVC COUNTRIES TIER ANALYSIS REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Load detailed data
    print("Loading VP data...")
    df = pd.read_excel(DATA_FILE, sheet_name='VP_2025_QVC.csv')
    print(f"Loaded {len(df):,} records")
    print()
    
    # Get unique nationalities
    nationalities = df['nationality_name_en'].unique()
    print(f"Countries with QVC offices: {', '.join(nationalities)}")
    print()
    
    # Analyze each nationality
    all_reports = []
    summary_data = []
    
    for nat_name in sorted(nationalities):
        nat_df = df[df['nationality_name_en'] == nat_name]
        report, summary = generate_nationality_report(nat_name, nat_df)
        all_reports.append(report)
        summary_data.append(summary)
    
    # Generate summary report
    summary_report = generate_summary_report(summary_data)
    
    # Save reports
    REPORT_DIR.mkdir(exist_ok=True)
    
    # Individual reports
    for report, summary in zip(all_reports, summary_data):
        filename = f"qvc_tier_report_{summary['name'].lower().replace(' ', '_')}_2025.txt"
        filepath = REPORT_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Saved: {filename}")
    
    # Combined report
    combined = "\n\n".join(all_reports)
    combined_path = REPORT_DIR / "qvc_tier_report_all_countries_2025.txt"
    with open(combined_path, 'w', encoding='utf-8') as f:
        f.write(combined)
    print(f"Saved: qvc_tier_report_all_countries_2025.txt")
    
    # Summary report
    summary_path = REPORT_DIR / "qvc_executive_summary_2025.txt"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_report)
    print(f"Saved: qvc_executive_summary_2025.txt")
    
    print()
    print("=" * 80)
    print("[OK] All QVC reports generated!")
    print("=" * 80)
    print()
    
    # Print summary to console
    print(summary_report)
    
    return summary_data


def generate_nationality_report(nat_name: str, df: pd.DataFrame) -> tuple:
    """Generate detailed report for a single nationality."""
    lines = []
    
    # Aggregate by profession
    prof_data = df.groupby(['profession_code', 'profession_name_en']).agg({
        'total_vp': 'sum',
        'used_vp': 'sum',
        'unused_vp': 'sum'
    }).reset_index()
    
    # Calculate totals
    total_vp = prof_data['total_vp'].sum()
    used_vp = prof_data['used_vp'].sum()
    unused_vp = prof_data['unused_vp'].sum()
    utilization = used_vp / total_vp if total_vp > 0 else 0
    
    # Count establishments
    num_establishments = df['est_moi_code'].nunique()
    
    # Size category distribution
    size_dist = df.groupby('size_category')['total_vp'].sum().to_dict()
    
    # Calculate tier classification
    prof_data['share'] = prof_data['total_vp'] / total_vp
    prof_data['tier'] = prof_data['share'].apply(lambda x: calculate_tier(x)[0])
    prof_data['tier_name'] = prof_data['share'].apply(lambda x: calculate_tier(x)[1])
    
    # Sort by total VP
    prof_data = prof_data.sort_values('total_vp', ascending=False)
    
    # Tier summaries
    tier_summary = {1: {'count': 0, 'vp': 0, 'profs': []},
                    2: {'count': 0, 'vp': 0, 'profs': []},
                    3: {'count': 0, 'vp': 0, 'profs': []},
                    4: {'count': 0, 'vp': 0, 'profs': []}}
    
    for _, row in prof_data.iterrows():
        tier = row['tier']
        tier_summary[tier]['count'] += 1
        tier_summary[tier]['vp'] += row['total_vp']
        if len(tier_summary[tier]['profs']) < 10:  # Keep top 10 per tier
            tier_summary[tier]['profs'].append({
                'name': row['profession_name_en'],
                'code': row['profession_code'],
                'total_vp': row['total_vp'],
                'used_vp': row['used_vp'],
                'share': row['share'],
                'usage': row['used_vp'] / row['total_vp'] if row['total_vp'] > 0 else 0
            })
    
    # Check for dominance alerts
    alerts = []
    for _, row in prof_data.iterrows():
        if row['share'] >= 0.30:
            level = "CRITICAL" if row['share'] >= 0.50 else "HIGH" if row['share'] >= 0.40 else "WATCH"
            alerts.append({
                'name': row['profession_name_en'],
                'share': row['share'],
                'level': level,
                'is_blocking': row['share'] >= 0.50
            })
    
    # Build report
    lines.append("=" * 80)
    lines.append(f"  {nat_name.upper()} - QVC TIER ANALYSIS REPORT")
    lines.append(f"  Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")
    
    # Section 1: Executive Summary
    lines.append("-" * 80)
    lines.append("  SECTION 1: EXECUTIVE SUMMARY")
    lines.append("-" * 80)
    lines.append("")
    lines.append("  KEY PERFORMANCE INDICATORS")
    lines.append("  +" + "-" * 76 + "+")
    lines.append(f"  | {'Metric':<35} | {'Value':>18} | {'Status':>15} |")
    lines.append("  +" + "-" * 76 + "+")
    lines.append(f"  | {'Total VP Allocated':<35} | {total_vp:>18,} | {'Capacity':>15} |")
    lines.append(f"  | {'VP Used':<35} | {used_vp:>18,} | {utilization*100:>14.1f}% |")
    lines.append(f"  | {'VP Unused (Available)':<35} | {unused_vp:>18,} | {'Headroom':>15} |")
    lines.append(f"  | {'Number of Establishments':<35} | {num_establishments:>18,} | {'Employers':>15} |")
    lines.append(f"  | {'Number of Professions':<35} | {len(prof_data):>18,} | {'Diversity':>15} |")
    lines.append("  +" + "-" * 76 + "+")
    lines.append("")
    
    # Utilization bar
    util_bar_len = 50
    filled = int(utilization * util_bar_len)
    bar = "[" + "#" * filled + "-" * (util_bar_len - filled) + "]"
    lines.append(f"  VP UTILIZATION: {bar} {utilization*100:.1f}%")
    lines.append(f"                  0%{' ' * 22}50%{' ' * 21}100%")
    lines.append("")
    
    # Size distribution
    lines.append("  ESTABLISHMENT SIZE DISTRIBUTION:")
    for size in ['Large', 'Medium', 'Small']:
        vp = size_dist.get(size, 0)
        pct = vp / total_vp * 100 if total_vp > 0 else 0
        lines.append(f"    {size:<10}: {vp:>12,} VP ({pct:>5.1f}%)")
    lines.append("")
    
    # Section 2: Tier Classification
    lines.append("-" * 80)
    lines.append("  SECTION 2: TIER CLASSIFICATION & STATUS")
    lines.append("-" * 80)
    lines.append("")
    
    lines.append("  TIER SUMMARY")
    lines.append("  +" + "-" * 18 + "+" + "-" * 12 + "+" + "-" * 15 + "+" + "-" * 12 + "+" + "-" * 12 + "+")
    lines.append(f"  | {'Tier':<16} | {'Profs':>10} | {'Total VP':>13} | {'Share %':>10} | {'Usage %':>10} |")
    lines.append("  +" + "-" * 18 + "+" + "-" * 12 + "+" + "-" * 15 + "+" + "-" * 12 + "+" + "-" * 12 + "+")
    
    tier_names = {1: "Tier 1 (Primary)", 2: "Tier 2 (Secondary)", 3: "Tier 3 (Minor)", 4: "Tier 4 (Unusual)"}
    for tier_level in [1, 2, 3, 4]:
        ts = tier_summary[tier_level]
        tier_share = ts['vp'] / total_vp * 100 if total_vp > 0 else 0
        tier_usage = sum(p['used_vp'] for p in ts['profs']) / ts['vp'] * 100 if ts['vp'] > 0 else 0
        lines.append(f"  | {tier_names[tier_level]:<16} | {ts['count']:>10,} | {ts['vp']:>13,} | {tier_share:>9.1f}% | {tier_usage:>9.1f}% |")
    
    lines.append("  +" + "-" * 18 + "+" + "-" * 12 + "+" + "-" * 15 + "+" + "-" * 12 + "+" + "-" * 12 + "+")
    lines.append("")
    
    # Top professions per tier
    lines.append("  TOP PROFESSIONS BY TIER")
    lines.append("")
    
    for tier_level in [1, 2, 3, 4]:
        tier_name_full = ["Primary (>15%)", "Secondary (5-15%)", "Minor (1-5%)", "Unusual (<1%)"][tier_level-1]
        tier_profs = tier_summary[tier_level]['profs'][:5]
        
        if tier_profs:
            lines.append(f"    TIER {tier_level} - {tier_name_full}")
            for p in tier_profs:
                usage_pct = p['usage'] * 100
                lines.append(f"      - {p['name'][:35]:<35} {p['total_vp']:>8,} VP ({p['share']*100:>5.1f}%) | Usage: {usage_pct:>5.1f}%")
            lines.append("")
    
    # Section 3: Dominance Risk
    lines.append("-" * 80)
    lines.append("  SECTION 3: DOMINANCE RISK ASSESSMENT")
    lines.append("-" * 80)
    lines.append("")
    
    if alerts:
        lines.append("  ACTIVE DOMINANCE ALERTS")
        lines.append("")
        for alert in alerts:
            level = alert["level"]
            icon = {"CRITICAL": "[!!!]", "HIGH": "[!!]", "WATCH": "[!]"}.get(level, "[?]")
            blocking = " ** BLOCKING NEW APPROVALS **" if alert["is_blocking"] else ""
            lines.append(f"    {icon} {level} ALERT{blocking}")
            lines.append(f"        Profession: {alert['name']}")
            lines.append(f"        Share: {alert['share']*100:.1f}%")
            lines.append("")
    else:
        lines.append("  [OK] No active dominance alerts")
        lines.append("  All professions are below the 30% concentration threshold.")
    lines.append("")
    
    # Section 4: Top 20 Professions
    lines.append("-" * 80)
    lines.append("  SECTION 4: TOP 20 PROFESSIONS BY VP ALLOCATION")
    lines.append("-" * 80)
    lines.append("")
    lines.append(f"  {'#':<3} {'Profession':<35} {'Tier':<6} {'Total VP':>10} {'Used':>10} {'Usage%':>8} {'Share%':>8}")
    lines.append("  " + "-" * 85)
    
    for i, (_, row) in enumerate(prof_data.head(20).iterrows(), 1):
        usage = row['used_vp'] / row['total_vp'] * 100 if row['total_vp'] > 0 else 0
        lines.append(f"  {i:<3} {row['profession_name_en'][:35]:<35} T{row['tier']:<5} {row['total_vp']:>10,} {row['used_vp']:>10,} {usage:>7.1f}% {row['share']*100:>7.1f}%")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("  END OF REPORT")
    lines.append("=" * 80)
    lines.append("")
    
    # Summary data for comparison
    summary = {
        'name': nat_name,
        'total_vp': total_vp,
        'used_vp': used_vp,
        'unused_vp': unused_vp,
        'utilization': utilization,
        'num_establishments': num_establishments,
        'num_professions': len(prof_data),
        'tier_summary': tier_summary,
        'alerts': alerts,
        'top_profs': [
            {
                'name': row['profession_name_en'],
                'total_vp': row['total_vp'],
                'share': row['share'],
                'tier': row['tier']
            }
            for _, row in prof_data.head(10).iterrows()
        ]
    }
    
    return "\n".join(lines), summary


def generate_summary_report(summary_data: list) -> str:
    """Generate executive summary comparing all QVC countries."""
    lines = []
    
    lines.append("=" * 100)
    lines.append("  QVC COUNTRIES - EXECUTIVE SUMMARY REPORT")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("  Countries: Bangladesh, India, Nepal, Pakistan, Philippines, Sri Lanka")
    lines.append("=" * 100)
    lines.append("")
    
    # Comparative table
    lines.append("-" * 100)
    lines.append("  COMPARATIVE ANALYSIS")
    lines.append("-" * 100)
    lines.append("")
    lines.append(f"  {'Country':<12} {'Total VP':>12} {'Used VP':>12} {'Unused VP':>12} {'Usage%':>10} {'Estabs':>10} {'Profs':>8} {'Alerts':>8}")
    lines.append("  " + "-" * 98)
    
    total_vp_all = 0
    total_used_all = 0
    
    for s in summary_data:
        total_vp_all += s['total_vp']
        total_used_all += s['used_vp']
        lines.append(f"  {s['name']:<12} {s['total_vp']:>12,} {s['used_vp']:>12,} {s['unused_vp']:>12,} {s['utilization']*100:>9.1f}% {s['num_establishments']:>10,} {s['num_professions']:>8,} {len(s['alerts']):>8}")
    
    lines.append("  " + "-" * 98)
    lines.append(f"  {'TOTAL':<12} {total_vp_all:>12,} {total_used_all:>12,} {total_vp_all-total_used_all:>12,} {total_used_all/total_vp_all*100:>9.1f}%")
    lines.append("")
    
    # Tier 1 professions by country
    lines.append("-" * 100)
    lines.append("  TIER 1 (PRIMARY >15%) PROFESSIONS BY COUNTRY")
    lines.append("-" * 100)
    lines.append("")
    
    for s in summary_data:
        tier1 = [p for p in s['top_profs'] if p['tier'] == 1]
        if tier1:
            lines.append(f"  {s['name']}:")
            for p in tier1:
                lines.append(f"    - {p['name'][:45]:<45} {p['total_vp']:>8,} VP ({p['share']*100:.1f}%)")
            lines.append("")
        else:
            lines.append(f"  {s['name']}: No Tier 1 professions (diversified workforce)")
            lines.append("")
    
    # Dominance alerts
    lines.append("-" * 100)
    lines.append("  DOMINANCE ALERTS SUMMARY")
    lines.append("-" * 100)
    lines.append("")
    
    has_alerts = False
    for s in summary_data:
        if s['alerts']:
            has_alerts = True
            lines.append(f"  {s['name']}:")
            for alert in s['alerts']:
                icon = {"CRITICAL": "[!!!]", "HIGH": "[!!]", "WATCH": "[!]"}.get(alert['level'], "")
                lines.append(f"    {icon} {alert['level']}: {alert['name'][:40]} - {alert['share']*100:.1f}%")
            lines.append("")
    
    if not has_alerts:
        lines.append("  [OK] No dominance alerts across all QVC countries.")
        lines.append("")
    
    # Usage efficiency ranking
    lines.append("-" * 100)
    lines.append("  VP USAGE EFFICIENCY RANKING")
    lines.append("-" * 100)
    lines.append("")
    
    sorted_by_usage = sorted(summary_data, key=lambda x: x['utilization'], reverse=True)
    for i, s in enumerate(sorted_by_usage, 1):
        status = "HIGH" if s['utilization'] > 0.70 else "MODERATE" if s['utilization'] > 0.40 else "LOW"
        lines.append(f"  {i}. {s['name']:<12}: {s['utilization']*100:>5.1f}% usage ({status})")
    
    lines.append("")
    lines.append("  NOTE: Higher usage indicates establishments are actively using allocated VPs.")
    lines.append("        Lower usage may indicate over-allocation or unused capacity.")
    lines.append("")
    
    lines.append("=" * 100)
    lines.append("  END OF EXECUTIVE SUMMARY")
    lines.append("=" * 100)
    
    return "\n".join(lines)


if __name__ == "__main__":
    analyze_qvc_data()
