#!/usr/bin/env python
"""
Iran Tier Analysis Report.

Generates detailed tier classification report for Iran based on worker stock data.
"""

import csv
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Paths
REAL_DATA_DIR = Path('real_data')
REPORT_DIR = Path('reports')

# Iran ISO code
IRAN_CODE = '364'


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


def load_professions() -> dict:
    """Load profession code to name mapping."""
    profs = {}
    with open(REAL_DATA_DIR / '02_professions.csv', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            code = row.get('code', '')
            name = row.get('name_en', '') or row.get('name', '') or f'Profession_{code}'
            profs[code] = name
    return profs


def load_activities() -> dict:
    """Load activity code to name mapping."""
    acts = {}
    with open(REAL_DATA_DIR / '03_economic_activities.csv', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            code = row.get('code', '')
            name = row.get('name_en', '') or row.get('name', '') or f'Activity_{code}'
            acts[code] = name
    return acts


def load_caps() -> dict:
    """Load nationality caps."""
    caps = {}
    with open(REAL_DATA_DIR / '05_nationality_caps.csv', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            nat_code = row.get('nationality_code', '')
            if nat_code:
                caps[nat_code] = {
                    'current_cap': int(row.get('current_cap', 0) or 0),
                    'previous_cap': int(row.get('previous_cap', 0) or 0),
                    'base_cap': int(row.get('base_cap', 0) or 0),
                }
    return caps


def analyze_iran():
    """Analyze Iran worker data and generate report."""
    print("=" * 80)
    print("IRAN TIER ANALYSIS REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Load reference data
    print("Loading reference data...")
    profs = load_professions()
    acts = load_activities()
    caps = load_caps()
    
    # Load worker stock
    print("Loading worker stock data...")
    with open(REAL_DATA_DIR / '07_worker_stock.csv', encoding='utf-8') as f:
        all_workers = list(csv.DictReader(f))
    
    # Filter Iran workers (ACTIVE only)
    iran_workers = [w for w in all_workers 
                    if (w.get('nationality_code') == IRAN_CODE or w.get('nationality') == IRAN_CODE)
                    and w.get('state', '').upper() in ('ACTIVE', 'IN_COUNTRY', '')]
    
    print(f"Iran workers (active): {len(iran_workers)}")
    print()
    
    # Get cap info
    iran_cap = caps.get(IRAN_CODE, {})
    current_cap = iran_cap.get('current_cap', 0)
    previous_cap = iran_cap.get('previous_cap', 0)
    
    # Aggregate by profession
    prof_counts = defaultdict(int)
    for w in iran_workers:
        prof_code = w.get('profession_code', 'Unknown')
        prof_counts[prof_code] += 1
    
    # Calculate totals and shares
    total_workers = len(iran_workers)
    prof_data = []
    
    for code, count in prof_counts.items():
        share = count / total_workers if total_workers > 0 else 0
        tier, tier_name, tier_range = calculate_tier(share)
        prof_data.append({
            'code': code,
            'name': profs.get(code, f'Code_{code}'),
            'count': count,
            'share': share,
            'tier': tier,
            'tier_name': tier_name
        })
    
    # Sort by count
    prof_data.sort(key=lambda x: -x['count'])
    
    # Tier summaries
    tier_summary = {1: {'count': 0, 'workers': 0, 'profs': []},
                    2: {'count': 0, 'workers': 0, 'profs': []},
                    3: {'count': 0, 'workers': 0, 'profs': []},
                    4: {'count': 0, 'workers': 0, 'profs': []}}
    
    for p in prof_data:
        tier = p['tier']
        tier_summary[tier]['count'] += 1
        tier_summary[tier]['workers'] += p['count']
        if len(tier_summary[tier]['profs']) < 10:
            tier_summary[tier]['profs'].append(p)
    
    # Aggregate by activity
    activity_counts = defaultdict(int)
    for w in iran_workers:
        act_code = w.get('activity_code', 'Unknown')
        activity_counts[act_code] += 1
    
    activity_data = [(acts.get(code, f'Activity_{code}'), count) 
                     for code, count in activity_counts.items()]
    activity_data.sort(key=lambda x: -x[1])
    
    # Check for dominance alerts
    alerts = []
    for p in prof_data:
        if p['share'] >= 0.30:
            level = "CRITICAL" if p['share'] >= 0.50 else "HIGH" if p['share'] >= 0.40 else "WATCH"
            alerts.append({
                'name': p['name'],
                'share': p['share'],
                'level': level,
                'is_blocking': p['share'] >= 0.50
            })
    
    # Calculate utilization
    utilization = total_workers / current_cap if current_cap > 0 else 0
    headroom = current_cap - total_workers if current_cap > 0 else 0
    
    # Calculate growth
    growth_pct = ((current_cap - previous_cap) / previous_cap * 100) if previous_cap > 0 else 0
    
    # Generate report
    report = generate_report(
        total_workers=total_workers,
        current_cap=current_cap,
        previous_cap=previous_cap,
        headroom=headroom,
        utilization=utilization,
        growth_pct=growth_pct,
        num_professions=len(prof_data),
        prof_data=prof_data,
        tier_summary=tier_summary,
        activity_data=activity_data,
        alerts=alerts
    )
    
    # Save report
    REPORT_DIR.mkdir(exist_ok=True)
    
    # Text report
    txt_path = REPORT_DIR / "iran_tier_analysis_2026.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Saved: {txt_path}")
    
    # Markdown report
    md_report = generate_markdown_report(
        total_workers=total_workers,
        current_cap=current_cap,
        previous_cap=previous_cap,
        headroom=headroom,
        utilization=utilization,
        growth_pct=growth_pct,
        num_professions=len(prof_data),
        prof_data=prof_data,
        tier_summary=tier_summary,
        activity_data=activity_data,
        alerts=alerts
    )
    
    md_path = REPORT_DIR / "Iran_Tier_Analysis_2026.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"Saved: {md_path}")
    
    print()
    print("=" * 80)
    print("[OK] Iran report generated!")
    print("=" * 80)
    print()
    
    # Print summary
    print(report)


def generate_report(**data) -> str:
    """Generate text report."""
    lines = []
    
    lines.append("=" * 80)
    lines.append("  IRAN - TIER ANALYSIS REPORT")
    lines.append(f"  Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("  Data Source: Ministry Worker Stock Data")
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
    lines.append(f"  | {'Total Active Workers':<35} | {data['total_workers']:>18,} | {'Current Stock':>15} |")
    lines.append(f"  | {'Current Cap':<35} | {data['current_cap']:>18,} | {'Limit':>15} |")
    lines.append(f"  | {'Previous Cap':<35} | {data['previous_cap']:>18,} | {'Prior Year':>15} |")
    lines.append(f"  | {'Available Headroom':<35} | {data['headroom']:>18,} | {'Capacity':>15} |")
    lines.append(f"  | {'Number of Professions':<35} | {data['num_professions']:>18,} | {'Diversity':>15} |")
    lines.append("  +" + "-" * 76 + "+")
    lines.append("")
    
    # Utilization bar
    util = data['utilization']
    util_bar_len = 50
    filled = int(min(util, 1.0) * util_bar_len)
    bar = "[" + "#" * filled + "-" * (util_bar_len - filled) + "]"
    lines.append(f"  CAP UTILIZATION: {bar} {util*100:.1f}%")
    lines.append(f"                   0%{' ' * 22}50%{' ' * 21}100%")
    lines.append("")
    
    # Growth
    growth = data['growth_pct']
    growth_indicator = "+" if growth > 0 else ""
    lines.append(f"  CAP GROWTH: {growth_indicator}{growth:.1f}% from previous year")
    lines.append("")
    
    # Section 2: Tier Classification
    lines.append("-" * 80)
    lines.append("  SECTION 2: TIER CLASSIFICATION & STATUS")
    lines.append("-" * 80)
    lines.append("")
    
    lines.append("  TIER SUMMARY")
    lines.append("  +" + "-" * 18 + "+" + "-" * 12 + "+" + "-" * 15 + "+" + "-" * 12 + "+")
    lines.append(f"  | {'Tier':<16} | {'Profs':>10} | {'Workers':>13} | {'Share %':>10} |")
    lines.append("  +" + "-" * 18 + "+" + "-" * 12 + "+" + "-" * 15 + "+" + "-" * 12 + "+")
    
    tier_names = {1: "Tier 1 (Primary)", 2: "Tier 2 (Secondary)", 3: "Tier 3 (Minor)", 4: "Tier 4 (Unusual)"}
    total = data['total_workers']
    for tier_level in [1, 2, 3, 4]:
        ts = data['tier_summary'][tier_level]
        tier_share = ts['workers'] / total * 100 if total > 0 else 0
        lines.append(f"  | {tier_names[tier_level]:<16} | {ts['count']:>10,} | {ts['workers']:>13,} | {tier_share:>9.1f}% |")
    
    lines.append("  +" + "-" * 18 + "+" + "-" * 12 + "+" + "-" * 15 + "+" + "-" * 12 + "+")
    lines.append("")
    
    # Top professions per tier
    lines.append("  TOP PROFESSIONS BY TIER")
    lines.append("")
    
    for tier_level in [1, 2, 3, 4]:
        tier_name_full = ["Primary (>15%)", "Secondary (5-15%)", "Minor (1-5%)", "Unusual (<1%)"][tier_level-1]
        tier_profs = data['tier_summary'][tier_level]['profs'][:5]
        
        if tier_profs:
            lines.append(f"    TIER {tier_level} - {tier_name_full}")
            for p in tier_profs:
                lines.append(f"      - {p['name'][:35]:<35} {p['count']:>8,} workers ({p['share']*100:>5.1f}%)")
            lines.append("")
    
    # Section 3: Dominance Risk
    lines.append("-" * 80)
    lines.append("  SECTION 3: DOMINANCE RISK ASSESSMENT")
    lines.append("-" * 80)
    lines.append("")
    
    if data['alerts']:
        lines.append("  ACTIVE DOMINANCE ALERTS")
        lines.append("")
        for alert in data['alerts']:
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
    lines.append("  SECTION 4: TOP 20 PROFESSIONS BY WORKER COUNT")
    lines.append("-" * 80)
    lines.append("")
    lines.append(f"  {'#':<3} {'Profession':<40} {'Tier':<6} {'Workers':>10} {'Share%':>8}")
    lines.append("  " + "-" * 70)
    
    for i, p in enumerate(data['prof_data'][:20], 1):
        lines.append(f"  {i:<3} {p['name'][:40]:<40} T{p['tier']:<5} {p['count']:>10,} {p['share']*100:>7.1f}%")
    
    lines.append("")
    
    # Section 5: Economic Activities
    lines.append("-" * 80)
    lines.append("  SECTION 5: TOP 10 ECONOMIC ACTIVITIES")
    lines.append("-" * 80)
    lines.append("")
    lines.append(f"  {'#':<3} {'Activity':<50} {'Workers':>10} {'Share%':>8}")
    lines.append("  " + "-" * 75)
    
    for i, (name, count) in enumerate(data['activity_data'][:10], 1):
        share = count / data['total_workers'] * 100 if data['total_workers'] > 0 else 0
        lines.append(f"  {i:<3} {name[:50]:<50} {count:>10,} {share:>7.1f}%")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("  END OF REPORT")
    lines.append("=" * 80)
    
    return "\n".join(lines)


def generate_markdown_report(**data) -> str:
    """Generate markdown report."""
    lines = []
    
    lines.append("# Iran Tier Analysis Report 2026")
    lines.append("")
    lines.append(f"**Report Generated:** {datetime.now().strftime('%B %d, %Y')}")
    lines.append("**Data Source:** Ministry Worker Stock Data")
    lines.append("**Nationality:** Iran (ISO Code: 364)")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("### Key Metrics at a Glance")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| **Total Active Workers** | {data['total_workers']:,} |")
    lines.append(f"| **Current Cap** | {data['current_cap']:,} |")
    lines.append(f"| **Previous Cap** | {data['previous_cap']:,} |")
    lines.append(f"| **Available Headroom** | {data['headroom']:,} |")
    lines.append(f"| **Cap Utilization** | {data['utilization']*100:.1f}% |")
    lines.append(f"| **Cap Growth** | {'+' if data['growth_pct'] > 0 else ''}{data['growth_pct']:.1f}% |")
    lines.append(f"| **Number of Professions** | {data['num_professions']:,} |")
    lines.append(f"| **Active Alerts** | {len(data['alerts'])} |")
    lines.append("")
    
    # Utilization bar
    util = data['utilization']
    filled = int(min(util, 1.0) * 50)
    bar = "#" * filled + "-" * (50 - filled)
    lines.append("### Cap Utilization")
    lines.append("")
    lines.append("```")
    lines.append(f"[{bar}] {util*100:.1f}%")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Tier Classification
    lines.append("## Tier Classification")
    lines.append("")
    lines.append("### Tier Definitions")
    lines.append("")
    lines.append("| Tier | Name | Share Range | Description |")
    lines.append("|------|------|-------------|-------------|")
    lines.append("| **Tier 1** | Primary | > 15% | Dominant professions requiring monitoring |")
    lines.append("| **Tier 2** | Secondary | 5% - 15% | Significant professions |")
    lines.append("| **Tier 3** | Minor | 1% - 5% | Regular professions |")
    lines.append("| **Tier 4** | Unusual | < 1% | Specialized/niche professions |")
    lines.append("")
    
    lines.append("### Tier Distribution")
    lines.append("")
    lines.append("| Tier | Professions | Workers | Share % |")
    lines.append("|------|-------------|---------|---------|")
    
    tier_names = {1: "Tier 1 (Primary)", 2: "Tier 2 (Secondary)", 3: "Tier 3 (Minor)", 4: "Tier 4 (Unusual)"}
    total = data['total_workers']
    for tier_level in [1, 2, 3, 4]:
        ts = data['tier_summary'][tier_level]
        tier_share = ts['workers'] / total * 100 if total > 0 else 0
        lines.append(f"| {tier_names[tier_level]} | {ts['count']:,} | {ts['workers']:,} | {tier_share:.1f}% |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Top Professions by Tier
    lines.append("## Top Professions by Tier")
    lines.append("")
    
    for tier_level in [1, 2, 3, 4]:
        tier_name_full = ["Primary (>15%)", "Secondary (5-15%)", "Minor (1-5%)", "Unusual (<1%)"][tier_level-1]
        tier_profs = data['tier_summary'][tier_level]['profs'][:5]
        
        lines.append(f"### Tier {tier_level} - {tier_name_full}")
        lines.append("")
        
        if tier_profs:
            lines.append("| Profession | Workers | Share % |")
            lines.append("|------------|---------|---------|")
            for p in tier_profs:
                lines.append(f"| {p['name']} | {p['count']:,} | {p['share']*100:.1f}% |")
        else:
            lines.append("*No professions in this tier - indicates good diversification*")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Dominance Risk
    lines.append("## Dominance Risk Assessment")
    lines.append("")
    
    if data['alerts']:
        lines.append("### Active Alerts")
        lines.append("")
        lines.append("| Profession | Share % | Alert Level | Status |")
        lines.append("|------------|---------|-------------|--------|")
        for alert in data['alerts']:
            status = "BLOCKING" if alert['is_blocking'] else "Monitor"
            lines.append(f"| **{alert['name']}** | **{alert['share']*100:.1f}%** | {alert['level']} | {status} |")
        lines.append("")
    else:
        lines.append("**Status:** No active alerts")
        lines.append("")
        lines.append("All professions are below the 30% concentration threshold. Iran demonstrates a well-diversified workforce distribution.")
        lines.append("")
    
    lines.append("### Alert Thresholds Reference")
    lines.append("")
    lines.append("| Level | Threshold | Action |")
    lines.append("|-------|-----------|--------|")
    lines.append("| **WATCH** | 30% - 39% | Monitor trends |")
    lines.append("| **HIGH** | 40% - 49% | Active intervention |")
    lines.append("| **CRITICAL** | 50%+ | Blocking new approvals |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Top 20 Professions
    lines.append("## Top 20 Professions by Worker Count")
    lines.append("")
    lines.append("| # | Profession | Tier | Workers | Share % |")
    lines.append("|---|------------|------|---------|---------|")
    
    for i, p in enumerate(data['prof_data'][:20], 1):
        lines.append(f"| {i} | {p['name']} | T{p['tier']} | {p['count']:,} | {p['share']*100:.1f}% |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Economic Activities
    lines.append("## Top 10 Economic Activities")
    lines.append("")
    lines.append("| # | Activity | Workers | Share % |")
    lines.append("|---|----------|---------|---------|")
    
    for i, (name, count) in enumerate(data['activity_data'][:10], 1):
        share = count / data['total_workers'] * 100 if data['total_workers'] > 0 else 0
        lines.append(f"| {i} | {name} | {count:,} | {share:.1f}% |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*End of Report*")
    
    return "\n".join(lines)


if __name__ == "__main__":
    analyze_iran()
