#!/usr/bin/env python
"""
Comprehensive Nationality Quota Report Generator.

Generates detailed reports for restricted nationalities including:
- Executive Summary & KPIs
- Cap Utilization Analysis
- Tier Status & Capacity
- Workforce Distribution by Profession
- Dominance Risk Assessment
- Growth Analysis & Projections
- AI Cap Recommendations
- Queue Analysis

Usage:
    python scripts/generate_comprehensive_report.py
"""

import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Data directory
DATA_DIR = Path(__file__).parent.parent / "real_data"
REPORT_DIR = Path(__file__).parent.parent / "reports"

# Target nationalities (ISO numeric codes)
TARGET_NATIONALITIES = {
    "818": "Egypt",
    "886": "Yemen", 
    "760": "Syria",
    "368": "Iraq",
    "004": "Afghanistan",
}

# Alternative codes
ALT_CODES = {"4": "Afghanistan"}


def load_csv(filename: str) -> list[dict]:
    """Load CSV file."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return []
    rows = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_reference_data():
    """Load all reference data."""
    print("Loading reference data...")
    
    # Nationalities
    nat_map = {}
    for row in load_csv("01_nationalities.csv"):
        code = row.get("code", "").strip()
        if code:
            nat_map[code] = {
                "name": row.get("name", "").strip(),
                "name_ar": row.get("name_ar", "").strip(),
                "is_restricted": row.get("is_restricted", "").lower() == "true",
            }
    
    # Professions
    prof_map = {}
    for row in load_csv("02_professions.csv"):
        code = row.get("code", "").strip()
        if code:
            prof_map[code] = {
                "name": row.get("name", "").strip(),
                "name_ar": row.get("name_ar", "").strip(),
                "category": row.get("category", "").strip(),
                "high_demand": row.get("high_demand_flag", "").lower() == "true",
            }
    
    # Caps
    caps = {}
    for row in load_csv("05_nationality_caps.csv"):
        code = row.get("nationality_code", "").strip().strip('"')
        try:
            caps[code] = {
                "cap_limit": int(row.get("cap_limit", 0)),
                "previous_cap": int(row.get("previous_cap", 0)),
            }
        except ValueError:
            pass
    
    print(f"  Loaded {len(nat_map)} nationalities, {len(prof_map)} professions, {len(caps)} caps")
    return nat_map, prof_map, caps


def analyze_workers(target_codes: set, prof_map: dict) -> dict:
    """Analyze worker stock for target nationalities."""
    print("Analyzing worker data (this may take a moment)...")
    
    results = defaultdict(lambda: {
        "in_country": 0,
        "out_country": 0,
        "committed": 0,
        "pending": 0,
        "total": 0,
        "professions": defaultdict(int),
        "prof_out": defaultdict(int),  # Track outflows by profession
        "recent_entries": 0,
        "recent_exits": 0,
        "employment_years": [],
    })
    
    filepath = DATA_DIR / "07_worker_stock.csv"
    if not filepath.exists():
        print(f"  [ERROR] Worker file not found")
        return results
    
    six_months_ago = datetime.now() - timedelta(days=180)
    row_count = 0
    
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_count += 1
            if row_count % 500000 == 0:
                print(f"    Processing row {row_count:,}...")
            
            nat_code = row.get("nationality_code", "").strip().strip('"')
            if nat_code not in target_codes:
                continue
            
            state = row.get("state", "").strip().upper()
            prof_code = row.get("profession_code", "").strip().strip('"')
            
            if state == "IN_COUNTRY":
                results[nat_code]["in_country"] += 1
                results[nat_code]["professions"][prof_code] += 1
            elif state == "OUT_COUNTRY":
                results[nat_code]["out_country"] += 1
                results[nat_code]["prof_out"][prof_code] += 1
            elif state == "COMMITTED":
                results[nat_code]["committed"] += 1
            elif state == "PENDING":
                results[nat_code]["pending"] += 1
            
            results[nat_code]["total"] += 1
            
            # Growth analysis
            emp_start = row.get("employment_start", "")
            emp_end = row.get("employment_end", "")
            
            try:
                if emp_start:
                    start_date = datetime.strptime(emp_start[:10], "%Y-%m-%d")
                    if start_date >= six_months_ago:
                        results[nat_code]["recent_entries"] += 1
                    # Track employment duration
                    years = (datetime.now() - start_date).days / 365
                    if 0 < years < 30:
                        results[nat_code]["employment_years"].append(years)
            except (ValueError, TypeError):
                pass
            
            try:
                if emp_end:
                    end_date = datetime.strptime(emp_end[:10], "%Y-%m-%d")
                    if end_date >= six_months_ago:
                        results[nat_code]["recent_exits"] += 1
            except (ValueError, TypeError):
                pass
    
    print(f"  Processed {row_count:,} worker records")
    return results


def calculate_tier(share_pct: float) -> tuple:
    """Calculate tier level and name."""
    if share_pct >= 0.15:
        return 1, "Primary", ">15%"
    elif share_pct >= 0.05:
        return 2, "Secondary", "5-15%"
    elif share_pct >= 0.01:
        return 3, "Minor", "1-5%"
    else:
        return 4, "Unusual", "<1%"


def get_tier_status(utilization: float, tier_level: int) -> str:
    """Determine tier status based on utilization."""
    if utilization > 0.95:
        return "CLOSED" if tier_level > 1 else "LIMITED"
    elif utilization > 0.90:
        if tier_level == 1:
            return "RATIONED"
        elif tier_level == 2:
            return "LIMITED"
        else:
            return "CLOSED"
    elif utilization > 0.85:
        if tier_level <= 2:
            return "OPEN"
        elif tier_level == 3:
            return "RATIONED"
        else:
            return "LIMITED"
    else:
        return "OPEN" if tier_level <= 3 else "RATIONED"


def analyze_dominance(professions: dict, total: int, prof_map: dict) -> list:
    """Analyze dominance risks by profession."""
    if total == 0:
        return []
    
    alerts = []
    for prof_code, count in professions.items():
        share = count / total
        if share >= 0.30:  # 30% threshold for alerts
            level = "CRITICAL" if share >= 0.50 else "HIGH" if share >= 0.40 else "WATCH"
            is_blocking = share >= 0.50
            
            prof_info = prof_map.get(prof_code, {})
            alerts.append({
                "code": prof_code,
                "name": prof_info.get("name", f"Unknown ({prof_code})"),
                "count": count,
                "share": share,
                "level": level,
                "is_blocking": is_blocking,
                "velocity": share * 0.15,  # Estimated velocity
            })
    
    return sorted(alerts, key=lambda x: x["share"], reverse=True)


def calculate_recommendation(stock: int, cap: int, growth_rate: float, alerts: list) -> dict:
    """Calculate AI cap recommendation."""
    utilization = stock / cap if cap > 0 else 0
    num_alerts = len(alerts)
    has_critical = any(a["level"] == "CRITICAL" for a in alerts)
    
    # Base recommendations
    conservative = int(cap * 1.05)
    moderate = int(cap * 1.10)
    flexible = int(cap * 1.20)
    
    # Determine recommendation level
    if has_critical or num_alerts > 3:
        level = "conservative"
        recommended = conservative
    elif utilization > 0.90 or num_alerts > 1:
        level = "moderate"
        recommended = moderate
    elif utilization < 0.80 and num_alerts == 0:
        level = "flexible"
        recommended = flexible
    else:
        level = "moderate"
        recommended = moderate
    
    # Adjust for growth
    if growth_rate > 0.05:  # Growing fast
        recommended = int(recommended * 1.05)
    elif growth_rate < -0.05:  # Declining
        recommended = int(recommended * 0.95)
    
    return {
        "conservative": conservative,
        "moderate": moderate,
        "flexible": flexible,
        "recommended": recommended,
        "level": level,
        "utilization": utilization,
    }


def generate_report_for_nationality(code: str, name: str, data: dict, 
                                     cap_info: dict, prof_map: dict) -> str:
    """Generate detailed report for a single nationality."""
    lines = []
    
    # Basic stats
    stock = data["in_country"]
    cap = cap_info.get("cap_limit", 0)
    prev_cap = cap_info.get("previous_cap", 0)
    headroom = cap - stock
    utilization = stock / cap if cap > 0 else 0
    
    # Growth
    net_change = data["recent_entries"] - data["recent_exits"]
    growth_rate = net_change / stock if stock > 0 else 0
    projected_annual = int(stock * growth_rate * 2)
    projected_stock = stock + projected_annual
    projected_outflow = int(stock * 0.045)  # ~4.5% quarterly outflow
    
    # Average employment duration
    avg_tenure = sum(data["employment_years"]) / len(data["employment_years"]) if data["employment_years"] else 0
    
    lines.append("=" * 80)
    lines.append(f"  {name.upper()} - COMPREHENSIVE QUOTA REPORT")
    lines.append(f"  Nationality Code: {code}")
    lines.append(f"  Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")
    
    # ============================================================
    # SECTION 1: EXECUTIVE SUMMARY
    # ============================================================
    lines.append("-" * 80)
    lines.append("  SECTION 1: EXECUTIVE SUMMARY")
    lines.append("-" * 80)
    lines.append("")
    lines.append("  KEY PERFORMANCE INDICATORS")
    lines.append("  +" + "-" * 76 + "+")
    lines.append(f"  | {'Metric':<30} | {'Value':>20} | {'Status':>18} |")
    lines.append("  +" + "-" * 76 + "+")
    lines.append(f"  | {'Annual Cap (2026)':<30} | {cap:>20,} | {'Set by Policy':>18} |")
    lines.append(f"  | {'Current Stock':<30} | {stock:>20,} | {utilization*100:>17.1f}% |")
    lines.append(f"  | {'Available Headroom':<30} | {headroom:>20,} | {'Capacity':>18} |")
    lines.append(f"  | {'Projected Outflow (90 days)':<30} | {projected_outflow:>20,} | {'Estimated':>18} |")
    lines.append("  +" + "-" * 76 + "+")
    lines.append("")
    
    # Utilization bar (text version)
    util_bar_len = 50
    filled = int(utilization * util_bar_len)
    bar = "[" + "#" * filled + "-" * (util_bar_len - filled) + "]"
    lines.append(f"  CAP UTILIZATION: {bar} {utilization*100:.1f}%")
    lines.append(f"                   0%{' ' * 22}50%{' ' * 21}100%")
    lines.append("")
    
    # ============================================================
    # SECTION 2: WORKFORCE COMPOSITION
    # ============================================================
    lines.append("-" * 80)
    lines.append("  SECTION 2: WORKFORCE COMPOSITION")
    lines.append("-" * 80)
    lines.append("")
    lines.append("  WORKER STATE DISTRIBUTION")
    lines.append(f"    In Country:      {data['in_country']:>12,}  ({data['in_country']/data['total']*100 if data['total'] > 0 else 0:>5.1f}%)")
    lines.append(f"    Out of Country:  {data['out_country']:>12,}  ({data['out_country']/data['total']*100 if data['total'] > 0 else 0:>5.1f}%)")
    lines.append(f"    Committed:       {data['committed']:>12,}  ({data['committed']/data['total']*100 if data['total'] > 0 else 0:>5.1f}%)")
    lines.append(f"    Pending:         {data['pending']:>12,}  ({data['pending']/data['total']*100 if data['total'] > 0 else 0:>5.1f}%)")
    lines.append(f"    {'='*40}")
    lines.append(f"    TOTAL RECORDS:   {data['total']:>12,}")
    lines.append("")
    
    if avg_tenure > 0:
        lines.append(f"  AVERAGE EMPLOYMENT TENURE: {avg_tenure:.1f} years")
        lines.append("")
    
    # ============================================================
    # SECTION 3: TIER CLASSIFICATION & STATUS
    # ============================================================
    lines.append("-" * 80)
    lines.append("  SECTION 3: TIER CLASSIFICATION & STATUS")
    lines.append("-" * 80)
    lines.append("")
    
    # Get top professions and classify by tier
    sorted_profs = sorted(data["professions"].items(), key=lambda x: x[1], reverse=True)
    
    tier_data = {1: [], 2: [], 3: [], 4: []}
    tier_totals = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for prof_code, count in sorted_profs:
        share = count / stock if stock > 0 else 0
        tier_level, tier_name, tier_range = calculate_tier(share)
        prof_info = prof_map.get(prof_code, {})
        tier_data[tier_level].append({
            "code": prof_code,
            "name": prof_info.get("name", f"Unknown ({prof_code})"),
            "count": count,
            "share": share,
        })
        tier_totals[tier_level] += count
    
    # Tier summary cards
    lines.append("  TIER STATUS SUMMARY")
    lines.append("  +" + "-" * 17 + "+" + "-" * 12 + "+" + "-" * 12 + "+" + "-" * 12 + "+" + "-" * 18 + "+")
    lines.append(f"  | {'Tier':<15} | {'Status':^10} | {'Workers':>10} | {'Share %':>10} | {'Capacity':>16} |")
    lines.append("  +" + "-" * 17 + "+" + "-" * 12 + "+" + "-" * 12 + "+" + "-" * 12 + "+" + "-" * 18 + "+")
    
    tier_names = {1: "Tier 1 (Primary)", 2: "Tier 2 (Secondary)", 3: "Tier 3 (Minor)", 4: "Tier 4 (Unusual)"}
    for tier_level in [1, 2, 3, 4]:
        status = get_tier_status(utilization, tier_level)
        tier_share = tier_totals[tier_level] / stock * 100 if stock > 0 else 0
        
        # Calculate capacity for this tier
        if status == "OPEN":
            capacity = int(headroom * [0.45, 0.30, 0.15, 0.10][tier_level-1])
        elif status == "RATIONED":
            capacity = int(headroom * [0.30, 0.20, 0.10, 0.05][tier_level-1])
        elif status == "LIMITED":
            capacity = int(headroom * [0.15, 0.10, 0.05, 0.02][tier_level-1])
        else:
            capacity = 0
        
        lines.append(f"  | {tier_names[tier_level]:<15} | {status:^10} | {tier_totals[tier_level]:>10,} | {tier_share:>9.1f}% | {capacity:>16,} |")
    
    lines.append("  +" + "-" * 17 + "+" + "-" * 12 + "+" + "-" * 12 + "+" + "-" * 12 + "+" + "-" * 18 + "+")
    lines.append("")
    
    # Top professions per tier
    lines.append("  TOP PROFESSIONS BY TIER")
    lines.append("")
    
    for tier_level in [1, 2, 3, 4]:
        tier_name_full = ["Primary (>15%)", "Secondary (5-15%)", "Minor (1-5%)", "Unusual (<1%)"][tier_level-1]
        tier_profs = tier_data[tier_level][:5]  # Top 5 per tier
        
        if tier_profs:
            lines.append(f"    TIER {tier_level} - {tier_name_full}")
            for p in tier_profs:
                lines.append(f"      - {p['name'][:40]:<40} {p['count']:>8,}  ({p['share']*100:>5.1f}%)")
            lines.append("")
    
    # ============================================================
    # SECTION 4: DOMINANCE RISK ASSESSMENT
    # ============================================================
    lines.append("-" * 80)
    lines.append("  SECTION 4: DOMINANCE RISK ASSESSMENT")
    lines.append("-" * 80)
    lines.append("")
    
    alerts = analyze_dominance(data["professions"], stock, prof_map)
    
    if alerts:
        lines.append("  ACTIVE DOMINANCE ALERTS")
        lines.append("")
        
        for alert in alerts:
            level = alert["level"]
            icon = {"CRITICAL": "[!!!]", "HIGH": "[!!]", "WATCH": "[!]"}.get(level, "[?]")
            blocking = " ** BLOCKING NEW APPROVALS **" if alert["is_blocking"] else ""
            
            lines.append(f"    {icon} {level} ALERT{blocking}")
            lines.append(f"        Profession: {alert['name']}")
            lines.append(f"        Share:      {alert['share']*100:.1f}% ({alert['count']:,} workers)")
            lines.append(f"        Velocity:   +{alert['velocity']*100:.1f}% per 3 years (estimated)")
            lines.append(f"        Threshold:  {'50%' if level == 'CRITICAL' else '40%' if level == 'HIGH' else '30%'}")
            lines.append("")
        
        lines.append("  DOMINANCE THRESHOLDS:")
        lines.append("    - WATCH:    30-40% share in profession")
        lines.append("    - HIGH:     40-50% share (partial approval only)")
        lines.append("    - CRITICAL: >50% share (blocks new approvals)")
    else:
        lines.append("  [OK] No active dominance alerts")
        lines.append("  All professions are below the 30% concentration threshold.")
    
    lines.append("")
    
    # ============================================================
    # SECTION 5: GROWTH ANALYSIS & PROJECTIONS
    # ============================================================
    lines.append("-" * 80)
    lines.append("  SECTION 5: GROWTH ANALYSIS & PROJECTIONS")
    lines.append("-" * 80)
    lines.append("")
    
    lines.append("  6-MONTH TREND ANALYSIS")
    lines.append(f"    New Entries:         {data['recent_entries']:>12,}")
    lines.append(f"    Exits:               {data['recent_exits']:>12,}")
    lines.append(f"    Net Change:          {net_change:>+12,}")
    lines.append(f"    Growth Rate:         {growth_rate*100:>+11.2f}%")
    lines.append("")
    
    lines.append("  12-MONTH PROJECTIONS")
    lines.append(f"    Projected Growth:    {projected_annual:>+12,}")
    lines.append(f"    Projected Stock:     {projected_stock:>12,}")
    lines.append(f"    Projected Headroom:  {cap - projected_stock:>12,}")
    lines.append(f"    Projected Util.:     {projected_stock/cap*100 if cap > 0 else 0:>11.1f}%")
    lines.append("")
    
    # Growth trend indicator
    if growth_rate > 0.02:
        trend = "GROWING - Workforce expanding"
    elif growth_rate < -0.02:
        trend = "DECLINING - Workforce contracting"
    else:
        trend = "STABLE - Minor fluctuations"
    
    lines.append(f"  TREND: {trend}")
    lines.append("")
    
    # ============================================================
    # SECTION 6: AI CAP RECOMMENDATION
    # ============================================================
    lines.append("-" * 80)
    lines.append("  SECTION 6: AI CAP RECOMMENDATION")
    lines.append("-" * 80)
    lines.append("")
    
    rec = calculate_recommendation(stock, cap, growth_rate, alerts)
    
    lines.append("  CAP OPTIONS ANALYSIS")
    lines.append("  +" + "-" * 20 + "+" + "-" * 15 + "+" + "-" * 15 + "+" + "-" * 20 + "+")
    lines.append(f"  | {'Option':<18} | {'Cap Value':>13} | {'Change':>13} | {'Growth Allowed':>18} |")
    lines.append("  +" + "-" * 20 + "+" + "-" * 15 + "+" + "-" * 15 + "+" + "-" * 20 + "+")
    
    for opt_name, opt_val in [("Conservative (+5%)", rec["conservative"]), 
                               ("Moderate (+10%)", rec["moderate"]),
                               ("Flexible (+20%)", rec["flexible"])]:
        change = opt_val - cap
        pct = change / cap * 100 if cap > 0 else 0
        lines.append(f"  | {opt_name:<18} | {opt_val:>13,} | {change:>+13,} | {pct:>+17.1f}% |")
    
    lines.append("  +" + "-" * 20 + "+" + "-" * 15 + "+" + "-" * 15 + "+" + "-" * 20 + "+")
    lines.append("")
    
    lines.append(f"  >>> RECOMMENDED: {rec['level'].upper()} - {rec['recommended']:,} <<<")
    lines.append("")
    
    # Rationale
    lines.append("  RECOMMENDATION RATIONALE:")
    if rec["level"] == "conservative":
        lines.append(f"    A conservative cap of {rec['conservative']:,} is recommended due to:")
        lines.append(f"    - {len(alerts)} active dominance alert(s)")
        lines.append(f"    - High utilization ({rec['utilization']*100:.1f}%)")
        lines.append("    - Need to maintain workforce diversification")
    elif rec["level"] == "flexible":
        lines.append(f"    A flexible cap of {rec['flexible']:,} is recommended due to:")
        lines.append(f"    - Low concentration risk ({len(alerts)} alerts)")
        lines.append(f"    - Healthy headroom available")
        lines.append("    - Room for expansion to meet demand")
    else:
        lines.append(f"    A moderate cap of {rec['moderate']:,} is recommended to:")
        lines.append(f"    - Balance growth with risk management")
        lines.append(f"    - Accommodate projected demand")
        lines.append(f"    - Monitor {len(alerts)} dominance concern(s)")
    
    lines.append("")
    lines.append("  KEY FACTORS:")
    lines.append(f"    - Current stock: {stock:,} workers")
    lines.append(f"    - Current cap: {cap:,}")
    lines.append(f"    - Utilization: {rec['utilization']*100:.1f}%")
    lines.append(f"    - Active alerts: {len(alerts)}")
    lines.append(f"    - Growth trend: {growth_rate*100:+.1f}%")
    lines.append("")
    
    lines.append("  RISKS:")
    if len(alerts) > 0:
        lines.append(f"    - {alerts[0]['level']} dominance risk in {alerts[0]['name']}")
    if rec["utilization"] > 0.85:
        lines.append("    - Near cap limit - may create processing backlogs")
    if growth_rate < -0.03:
        lines.append("    - Workforce declining - monitor for skill gaps")
    if not alerts and rec["utilization"] < 0.85:
        lines.append("    - No significant risks identified")
    
    lines.append("")
    
    # ============================================================
    # SECTION 7: CAP HISTORY
    # ============================================================
    lines.append("-" * 80)
    lines.append("  SECTION 7: CAP HISTORY")
    lines.append("-" * 80)
    lines.append("")
    
    cap_change = cap - prev_cap
    cap_pct = cap_change / prev_cap * 100 if prev_cap > 0 else 0
    
    lines.append(f"    2026 Cap:     {cap:>12,}")
    lines.append(f"    2025 Cap:     {prev_cap:>12,}")
    lines.append(f"    Change:       {cap_change:>+12,} ({cap_pct:+.1f}%)")
    lines.append("")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("  END OF REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append("")
    
    return "\n".join(lines)


def generate_summary_report(all_data: list) -> str:
    """Generate summary comparison across all nationalities."""
    lines = []
    
    lines.append("=" * 100)
    lines.append("  NATIONALITY QUOTA SYSTEM - EXECUTIVE SUMMARY REPORT")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("  Nationalities: Egypt, Yemen, Syria, Iraq, Afghanistan")
    lines.append("=" * 100)
    lines.append("")
    
    # Summary table
    lines.append("-" * 100)
    lines.append("  COMPARATIVE ANALYSIS")
    lines.append("-" * 100)
    lines.append("")
    lines.append(f"  {'Nationality':<12} {'Stock':>10} {'Cap':>10} {'Headroom':>10} {'Util%':>8} {'Growth':>8} {'Alerts':>8} {'Rec':>12} {'Suggested':>12}")
    lines.append("  " + "-" * 98)
    
    total_stock = 0
    total_cap = 0
    
    for entry in all_data:
        name = entry["name"][:10]
        stock = entry["stock"]
        cap = entry["cap"]
        headroom = entry["headroom"]
        util = entry["utilization"]
        growth = entry["growth_rate"]
        alerts = entry["alert_count"]
        rec_level = entry["rec_level"][:10]
        suggested = entry["recommended"]
        
        total_stock += stock
        total_cap += cap
        
        lines.append(f"  {name:<12} {stock:>10,} {cap:>10,} {headroom:>10,} {util:>7.1f}% {growth:>+7.1f}% {alerts:>8} {rec_level:>12} {suggested:>12,}")
    
    lines.append("  " + "-" * 98)
    lines.append(f"  {'TOTAL':<12} {total_stock:>10,} {total_cap:>10,} {total_cap-total_stock:>10,} {total_stock/total_cap*100:>7.1f}%")
    lines.append("")
    
    # Tier 1 professions
    lines.append("-" * 100)
    lines.append("  TIER 1 (PRIMARY) PROFESSIONS BY NATIONALITY")
    lines.append("-" * 100)
    lines.append("")
    
    for entry in all_data:
        tier1 = [p for p in entry["top_profs"] if p["tier"] == 1]
        if tier1:
            lines.append(f"  {entry['name']}:")
            for p in tier1:
                lines.append(f"    - {p['name'][:45]:<45} {p['count']:>8,} ({p['share']*100:.1f}%)")
            lines.append("")
    
    # Dominance alerts summary
    lines.append("-" * 100)
    lines.append("  DOMINANCE ALERTS SUMMARY")
    lines.append("-" * 100)
    lines.append("")
    
    has_alerts = False
    for entry in all_data:
        if entry["alerts"]:
            has_alerts = True
            lines.append(f"  {entry['name']}:")
            for alert in entry["alerts"]:
                icon = {"CRITICAL": "[!!!]", "HIGH": "[!!]", "WATCH": "[!]"}.get(alert["level"], "")
                lines.append(f"    {icon} {alert['level']}: {alert['name'][:35]} - {alert['share']*100:.1f}%")
            lines.append("")
    
    if not has_alerts:
        lines.append("  No critical dominance alerts across analyzed nationalities.")
        lines.append("")
    
    # Recommendations summary
    lines.append("-" * 100)
    lines.append("  CAP RECOMMENDATIONS SUMMARY")
    lines.append("-" * 100)
    lines.append("")
    lines.append(f"  {'Nationality':<15} {'Current Cap':>12} {'Recommended':>12} {'Change':>12} {'Level':>15}")
    lines.append("  " + "-" * 68)
    
    for entry in all_data:
        change = entry["recommended"] - entry["cap"]
        lines.append(f"  {entry['name']:<15} {entry['cap']:>12,} {entry['recommended']:>12,} {change:>+12,} {entry['rec_level']:>15}")
    
    lines.append("")
    lines.append("=" * 100)
    lines.append("  END OF EXECUTIVE SUMMARY")
    lines.append("=" * 100)
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    print("=" * 70)
    print("COMPREHENSIVE NATIONALITY QUOTA REPORT GENERATOR")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    # Ensure reports directory exists
    REPORT_DIR.mkdir(exist_ok=True)
    
    # Load reference data
    nat_map, prof_map, caps = load_reference_data()
    print()
    
    # Build target codes
    target_codes = set(TARGET_NATIONALITIES.keys())
    target_codes.update(ALT_CODES.keys())
    
    # Analyze workers
    worker_data = analyze_workers(target_codes, prof_map)
    print()
    
    # Generate reports
    all_reports = []
    summary_data = []
    
    for code, name in TARGET_NATIONALITIES.items():
        print(f"Generating report for {name}...")
        
        # Get data (try alternative codes)
        data = worker_data.get(code)
        if not data or data["in_country"] == 0:
            alt_code = code.lstrip("0")
            data = worker_data.get(alt_code)
            if data:
                code = alt_code
        
        if not data:
            print(f"  [WARN] No data found for {name}")
            continue
        
        # Get cap info
        cap_info = caps.get(code) or caps.get(code.zfill(3)) or {"cap_limit": 0, "previous_cap": 0}
        
        # Generate detailed report
        report = generate_report_for_nationality(code, name, data, cap_info, prof_map)
        all_reports.append(report)
        
        # Collect summary data
        stock = data["in_country"]
        cap = cap_info.get("cap_limit", 0)
        headroom = cap - stock
        utilization = stock / cap if cap > 0 else 0
        net_change = data["recent_entries"] - data["recent_exits"]
        growth_rate = net_change / stock * 100 if stock > 0 else 0
        
        # Top professions
        sorted_profs = sorted(data["professions"].items(), key=lambda x: x[1], reverse=True)
        top_profs = []
        for prof_code, count in sorted_profs[:10]:
            share = count / stock if stock > 0 else 0
            tier_level, _, _ = calculate_tier(share)
            prof_info = prof_map.get(prof_code, {})
            top_profs.append({
                "code": prof_code,
                "name": prof_info.get("name", f"Unknown ({prof_code})"),
                "count": count,
                "share": share,
                "tier": tier_level,
            })
        
        # Alerts
        alerts = analyze_dominance(data["professions"], stock, prof_map)
        
        # Recommendation
        rec = calculate_recommendation(stock, cap, growth_rate / 100, alerts)
        
        summary_data.append({
            "code": code,
            "name": name,
            "stock": stock,
            "cap": cap,
            "headroom": headroom,
            "utilization": utilization * 100,
            "growth_rate": growth_rate,
            "alert_count": len(alerts),
            "alerts": alerts,
            "top_profs": top_profs,
            "rec_level": rec["level"].title(),
            "recommended": rec["recommended"],
        })
    
    # Generate summary report
    print()
    print("Generating executive summary...")
    summary_report = generate_summary_report(summary_data)
    
    # Write reports
    print()
    print("Writing reports to files...")
    
    # Individual reports
    for i, report in enumerate(all_reports):
        nat_name = list(TARGET_NATIONALITIES.values())[i].lower()
        filepath = REPORT_DIR / f"quota_report_{nat_name}_2026.txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"  - {filepath.name}")
    
    # Combined report
    combined = "\n\n".join(all_reports)
    combined_path = REPORT_DIR / "quota_report_all_nationalities_2026.txt"
    with open(combined_path, "w", encoding="utf-8") as f:
        f.write(combined)
    print(f"  - {combined_path.name}")
    
    # Summary report
    summary_path = REPORT_DIR / "quota_executive_summary_2026.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_report)
    print(f"  - {summary_path.name}")
    
    print()
    print("=" * 70)
    print("[OK] All reports generated successfully!")
    print(f"Reports saved to: {REPORT_DIR}")
    print("=" * 70)
    
    # Print executive summary to console
    print()
    print(summary_report)


if __name__ == "__main__":
    main()
