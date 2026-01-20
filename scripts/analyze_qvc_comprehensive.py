#!/usr/bin/env python
"""
Comprehensive QVC Countries Analysis Report.

Analyzes worker stock data for the 6 QVC countries:
- India, Bangladesh, Nepal, Pakistan, Philippines, Sri Lanka

Generates detailed reports with:
- Current stock & utilization
- 4-tier classification by profession
- Growth analysis
- Dominant jobs assessment
- Cap recommendations
"""

import csv
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent.parent / "real_data"
REPORT_DIR = Path(__file__).parent.parent / "reports"

# Target QVC Countries (nationality codes)
QVC_COUNTRIES = {
    "356": "India",
    "50": "Bangladesh",
    "524": "Nepal",
    "586": "Pakistan",
    "608": "Philippines",
    "144": "Sri Lanka",
}

# Alternative codes (some may have leading zeros stripped)
ALT_CODES = {
    "050": "Bangladesh",
}


def load_csv(filename: str) -> list[dict]:
    """Load CSV file from real_data directory."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"[ERROR] File not found: {filepath}")
        return []
    rows = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_reference_data():
    """Load reference data (nationalities, professions, caps)."""
    print("Loading reference data...")
    
    # Nationalities
    nat_map = {}
    for row in load_csv("01_nationalities.csv"):
        code = row.get("code", "").strip()
        if code:
            nat_map[code] = {
                "name": row.get("name", "").strip(),
                "name_ar": row.get("name_ar", "").strip(),
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
    print("Analyzing worker stock data...")
    
    results = defaultdict(lambda: {
        "in_country": 0,
        "out_country": 0,
        "committed": 0,
        "pending": 0,
        "total": 0,
        "professions": defaultdict(int),
        "prof_out": defaultdict(int),
        "recent_entries": 0,
        "recent_exits": 0,
        "employment_years": [],
    })
    
    filepath = DATA_DIR / "07_worker_stock.csv"
    if not filepath.exists():
        print(f"  [ERROR] Worker stock file not found: {filepath}")
        return results
    
    six_months_ago = datetime.now() - timedelta(days=180)
    row_count = 0
    matched_count = 0
    
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_count += 1
            if row_count % 500000 == 0:
                print(f"    Processing row {row_count:,}...")
            
            # Get nationality code (handle quoted values)
            nat_code = row.get("nationality_code", "").strip().strip('"')
            
            # Check if this is a target nationality
            if nat_code not in target_codes:
                continue
            
            matched_count += 1
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
            
            # Growth analysis - recent entries/exits
            emp_start = row.get("employment_start", "")
            emp_end = row.get("employment_end", "")
            
            try:
                if emp_start:
                    start_date = datetime.strptime(emp_start[:10], "%Y-%m-%d")
                    if start_date >= six_months_ago:
                        results[nat_code]["recent_entries"] += 1
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
    
    print(f"  Processed {row_count:,} records, matched {matched_count:,} for target nationalities")
    return results


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
        if share >= 0.30:
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
    if growth_rate > 0.05:
        recommended = int(recommended * 1.05)
    elif growth_rate < -0.05:
        recommended = int(recommended * 0.95)
    
    return {
        "conservative": conservative,
        "moderate": moderate,
        "flexible": flexible,
        "recommended": recommended,
        "level": level,
        "utilization": utilization,
    }


def generate_country_report(code: str, name: str, data: dict, 
                            cap_info: dict, prof_map: dict) -> tuple:
    """Generate detailed report for a single country."""
    lines = []
    
    # Basic stats
    stock = data["in_country"]
    cap = cap_info.get("cap_limit", 0)
    prev_cap = cap_info.get("previous_cap", 0)
    headroom = cap - stock
    utilization = stock / cap if cap > 0 else 0
    
    # Growth calculations
    net_change = data["recent_entries"] - data["recent_exits"]
    growth_rate = net_change / stock if stock > 0 else 0
    projected_annual = int(stock * growth_rate * 2)
    projected_stock = stock + projected_annual
    projected_outflow = int(stock * 0.045)
    
    # Average tenure
    avg_tenure = sum(data["employment_years"]) / len(data["employment_years"]) if data["employment_years"] else 0
    
    # Tier classification
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
    
    # Dominance alerts
    alerts = analyze_dominance(data["professions"], stock, prof_map)
    
    # Cap recommendation
    rec = calculate_recommendation(stock, cap, growth_rate, alerts)
    
    # Build report
    lines.append("=" * 90)
    lines.append(f"  {name.upper()} - COMPREHENSIVE QUOTA ANALYSIS REPORT")
    lines.append(f"  Nationality Code: {code}")
    lines.append(f"  Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Data Source: D:\\Quota\\real_data\\07_worker_stock.csv")
    lines.append("=" * 90)
    lines.append("")
    
    # SECTION 1: EXECUTIVE SUMMARY
    lines.append("-" * 90)
    lines.append("  SECTION 1: EXECUTIVE SUMMARY")
    lines.append("-" * 90)
    lines.append("")
    lines.append("  KEY PERFORMANCE INDICATORS")
    lines.append("  +" + "-" * 86 + "+")
    lines.append(f"  | {'Metric':<35} | {'Value':>22} | {'Status':>20} |")
    lines.append("  +" + "-" * 86 + "+")
    lines.append(f"  | {'Annual Cap (2026)':<35} | {cap:>22,} | {'Policy Set':>20} |")
    lines.append(f"  | {'Current Stock (In-Country)':<35} | {stock:>22,} | {utilization*100:>19.1f}% |")
    lines.append(f"  | {'Available Headroom':<35} | {headroom:>22,} | {'Capacity':>20} |")
    lines.append(f"  | {'Out of Country':<35} | {data['out_country']:>22,} | {'Inactive':>20} |")
    lines.append(f"  | {'Committed/Pending':<35} | {data['committed']+data['pending']:>22,} | {'In Process':>20} |")
    lines.append(f"  | {'Total Records':<35} | {data['total']:>22,} | {'All States':>20} |")
    lines.append("  +" + "-" * 86 + "+")
    lines.append("")
    
    # Utilization bar
    util_bar_len = 50
    filled = int(min(utilization, 1.0) * util_bar_len)
    bar = "[" + "#" * filled + "-" * (util_bar_len - filled) + "]"
    lines.append(f"  CAP UTILIZATION: {bar} {utilization*100:.1f}%")
    lines.append(f"                   0%{' ' * 22}50%{' ' * 21}100%")
    lines.append("")
    
    # SECTION 2: WORKFORCE COMPOSITION
    lines.append("-" * 90)
    lines.append("  SECTION 2: WORKFORCE COMPOSITION")
    lines.append("-" * 90)
    lines.append("")
    lines.append("  WORKER STATE DISTRIBUTION")
    lines.append(f"    In Country:      {data['in_country']:>15,}  ({data['in_country']/data['total']*100 if data['total'] > 0 else 0:>5.1f}%)")
    lines.append(f"    Out of Country:  {data['out_country']:>15,}  ({data['out_country']/data['total']*100 if data['total'] > 0 else 0:>5.1f}%)")
    lines.append(f"    Committed:       {data['committed']:>15,}  ({data['committed']/data['total']*100 if data['total'] > 0 else 0:>5.1f}%)")
    lines.append(f"    Pending:         {data['pending']:>15,}  ({data['pending']/data['total']*100 if data['total'] > 0 else 0:>5.1f}%)")
    lines.append(f"    {'='*45}")
    lines.append(f"    TOTAL RECORDS:   {data['total']:>15,}")
    lines.append("")
    
    if avg_tenure > 0:
        lines.append(f"  AVERAGE EMPLOYMENT TENURE: {avg_tenure:.1f} years")
        lines.append("")
    
    lines.append(f"  UNIQUE PROFESSIONS: {len(data['professions']):,}")
    lines.append("")
    
    # SECTION 3: TIER CLASSIFICATION
    lines.append("-" * 90)
    lines.append("  SECTION 3: TIER CLASSIFICATION & STATUS")
    lines.append("-" * 90)
    lines.append("")
    
    lines.append("  TIER SUMMARY")
    lines.append("  +" + "-" * 20 + "+" + "-" * 12 + "+" + "-" * 15 + "+" + "-" * 12 + "+" + "-" * 20 + "+")
    lines.append(f"  | {'Tier':<18} | {'Status':^10} | {'Workers':>13} | {'Share %':>10} | {'Available':>18} |")
    lines.append("  +" + "-" * 20 + "+" + "-" * 12 + "+" + "-" * 15 + "+" + "-" * 12 + "+" + "-" * 20 + "+")
    
    tier_names = {1: "Tier 1 (Highest Demand)", 2: "Tier 2 (High Demand)", 3: "Tier 3 (Moderate)", 4: "Tier 4 (Low/Specialized)"}
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
        
        lines.append(f"  | {tier_names[tier_level]:<18} | {status:^10} | {tier_totals[tier_level]:>13,} | {tier_share:>9.1f}% | {capacity:>18,} |")
    
    lines.append("  +" + "-" * 20 + "+" + "-" * 12 + "+" + "-" * 15 + "+" + "-" * 12 + "+" + "-" * 20 + "+")
    lines.append("")
    
    # Top professions per tier
    lines.append("  TOP PROFESSIONS BY TIER")
    lines.append("")
    
    for tier_level in [1, 2, 3, 4]:
        tier_name_full = ["Highest Demand (>15%) - Priority Allocation", "High Demand (5-15%)", "Moderate Demand (1-5%)", "Low Demand (<1%)"][tier_level-1]
        tier_profs = tier_data[tier_level][:5]
        
        if tier_profs:
            lines.append(f"    TIER {tier_level} - {tier_name_full}")
            for p in tier_profs:
                lines.append(f"      - {p['name'][:45]:<45} {p['count']:>10,}  ({p['share']*100:>5.1f}%)")
            lines.append("")
    
    # SECTION 4: DOMINANT JOBS ANALYSIS
    lines.append("-" * 90)
    lines.append("  SECTION 4: DOMINANT JOBS ANALYSIS")
    lines.append("-" * 90)
    lines.append("")
    
    lines.append("  TOP 15 PROFESSIONS BY WORKER COUNT")
    lines.append(f"  {'#':<3} {'Profession':<45} {'Tier':<6} {'Workers':>12} {'Share %':>10}")
    lines.append("  " + "-" * 80)
    
    for i, (prof_code, count) in enumerate(sorted_profs[:15], 1):
        share = count / stock * 100 if stock > 0 else 0
        tier_level, _, _ = calculate_tier(count / stock if stock > 0 else 0)
        prof_info = prof_map.get(prof_code, {})
        prof_name = prof_info.get("name", f"Unknown ({prof_code})")
        lines.append(f"  {i:<3} {prof_name[:45]:<45} T{tier_level:<5} {count:>12,} {share:>9.1f}%")
    
    lines.append("")
    
    # SECTION 5: DOMINANCE RISK ASSESSMENT
    lines.append("-" * 90)
    lines.append("  SECTION 5: DOMINANCE RISK ASSESSMENT")
    lines.append("-" * 90)
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
            lines.append(f"        Share:      {alert['share']*100:.1f}% ({alert['count']:,} workers)")
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
    
    # SECTION 6: GROWTH ANALYSIS
    lines.append("-" * 90)
    lines.append("  SECTION 6: GROWTH ANALYSIS & PROJECTIONS")
    lines.append("-" * 90)
    lines.append("")
    
    lines.append("  6-MONTH TREND ANALYSIS")
    lines.append(f"    New Entries:         {data['recent_entries']:>15,}")
    lines.append(f"    Exits:               {data['recent_exits']:>15,}")
    lines.append(f"    Net Change:          {net_change:>+15,}")
    lines.append(f"    Growth Rate:         {growth_rate*100:>+14.2f}%")
    lines.append("")
    
    lines.append("  12-MONTH PROJECTIONS")
    lines.append(f"    Projected Growth:    {projected_annual:>+15,}")
    lines.append(f"    Projected Stock:     {projected_stock:>15,}")
    lines.append(f"    Projected Headroom:  {cap - projected_stock:>15,}")
    lines.append(f"    Projected Util.:     {projected_stock/cap*100 if cap > 0 else 0:>14.1f}%")
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
    
    # SECTION 7: CAP RECOMMENDATION
    lines.append("-" * 90)
    lines.append("  SECTION 7: AI CAP RECOMMENDATION")
    lines.append("-" * 90)
    lines.append("")
    
    lines.append("  CAP OPTIONS ANALYSIS")
    lines.append("  +" + "-" * 22 + "+" + "-" * 18 + "+" + "-" * 18 + "+" + "-" * 18 + "+")
    lines.append(f"  | {'Option':<20} | {'Cap Value':>16} | {'Change':>16} | {'Growth':>16} |")
    lines.append("  +" + "-" * 22 + "+" + "-" * 18 + "+" + "-" * 18 + "+" + "-" * 18 + "+")
    
    for opt_name, opt_val in [("Conservative (+5%)", rec["conservative"]), 
                               ("Moderate (+10%)", rec["moderate"]),
                               ("Flexible (+20%)", rec["flexible"])]:
        change = opt_val - cap
        pct = change / cap * 100 if cap > 0 else 0
        lines.append(f"  | {opt_name:<20} | {opt_val:>16,} | {change:>+16,} | {pct:>+15.1f}% |")
    
    lines.append("  +" + "-" * 22 + "+" + "-" * 18 + "+" + "-" * 18 + "+" + "-" * 18 + "+")
    lines.append("")
    
    lines.append(f"  >>> RECOMMENDED: {rec['level'].upper()} - {rec['recommended']:,} <<<")
    lines.append("")
    
    # Rationale
    lines.append("  RECOMMENDATION RATIONALE:")
    if rec["level"] == "conservative":
        lines.append(f"    A conservative cap increase is recommended due to:")
        lines.append(f"    - {len(alerts)} active dominance alert(s)")
        lines.append(f"    - Current utilization: {rec['utilization']*100:.1f}%")
        lines.append("    - Need to maintain workforce diversification")
    elif rec["level"] == "flexible":
        lines.append(f"    A flexible cap increase is recommended due to:")
        lines.append(f"    - No concentration risks ({len(alerts)} alerts)")
        lines.append(f"    - Low utilization: {rec['utilization']*100:.1f}%")
        lines.append("    - Room for growth to meet market demand")
    else:
        lines.append(f"    A moderate cap increase is recommended to:")
        lines.append(f"    - Balance growth with risk management")
        lines.append(f"    - Accommodate projected demand")
        lines.append(f"    - Current utilization: {rec['utilization']*100:.1f}%")
    
    lines.append("")
    
    # Cap history
    lines.append("-" * 90)
    lines.append("  SECTION 8: CAP HISTORY")
    lines.append("-" * 90)
    lines.append("")
    
    cap_change = cap - prev_cap
    cap_pct = cap_change / prev_cap * 100 if prev_cap > 0 else 0
    
    lines.append(f"    2026 Cap:     {cap:>15,}")
    lines.append(f"    2025 Cap:     {prev_cap:>15,}")
    lines.append(f"    YoY Change:   {cap_change:>+15,} ({cap_pct:+.1f}%)")
    lines.append("")
    
    lines.append("=" * 90)
    lines.append("  END OF REPORT")
    lines.append("=" * 90)
    lines.append("")
    
    # Summary data for executive summary
    summary = {
        "code": code,
        "name": name,
        "stock": stock,
        "cap": cap,
        "headroom": headroom,
        "utilization": utilization * 100,
        "out_country": data["out_country"],
        "total": data["total"],
        "num_professions": len(data["professions"]),
        "growth_rate": growth_rate * 100,
        "alert_count": len(alerts),
        "alerts": alerts,
        "tier_totals": tier_totals,
        "top_profs": [
            {
                "code": pc,
                "name": prof_map.get(pc, {}).get("name", f"Unknown ({pc})"),
                "count": cnt,
                "share": cnt / stock if stock > 0 else 0,
                "tier": calculate_tier(cnt / stock if stock > 0 else 0)[0],
            }
            for pc, cnt in sorted_profs[:10]
        ],
        "rec_level": rec["level"].title(),
        "recommended": rec["recommended"],
    }
    
    return "\n".join(lines), summary


def generate_executive_summary(summary_data: list) -> str:
    """Generate executive summary comparing all countries."""
    lines = []
    
    lines.append("=" * 110)
    lines.append("  QVC COUNTRIES - COMPREHENSIVE EXECUTIVE SUMMARY")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("  Data Source: D:\\Quota\\real_data\\07_worker_stock.csv")
    lines.append("  Countries: India, Bangladesh, Nepal, Pakistan, Philippines, Sri Lanka")
    lines.append("=" * 110)
    lines.append("")
    
    # Comparative table
    lines.append("-" * 110)
    lines.append("  COMPARATIVE ANALYSIS")
    lines.append("-" * 110)
    lines.append("")
    lines.append(f"  {'Country':<12} {'Stock':>12} {'Cap':>12} {'Headroom':>12} {'Util%':>10} {'Growth':>10} {'Alerts':>8} {'Rec Level':>12} {'Suggested':>14}")
    lines.append("  " + "-" * 108)
    
    total_stock = 0
    total_cap = 0
    
    for s in summary_data:
        total_stock += s["stock"]
        total_cap += s["cap"]
        lines.append(f"  {s['name']:<12} {s['stock']:>12,} {s['cap']:>12,} {s['headroom']:>12,} {s['utilization']:>9.1f}% {s['growth_rate']:>+9.1f}% {s['alert_count']:>8} {s['rec_level']:>12} {s['recommended']:>14,}")
    
    lines.append("  " + "-" * 108)
    lines.append(f"  {'TOTAL':<12} {total_stock:>12,} {total_cap:>12,} {total_cap-total_stock:>12,} {total_stock/total_cap*100 if total_cap > 0 else 0:>9.1f}%")
    lines.append("")
    
    # Utilization ranking
    lines.append("-" * 110)
    lines.append("  CAP UTILIZATION RANKING")
    lines.append("-" * 110)
    lines.append("")
    
    sorted_by_util = sorted(summary_data, key=lambda x: x["utilization"], reverse=True)
    for i, s in enumerate(sorted_by_util, 1):
        # Visual bar
        bar_len = 40
        filled = int(min(s["utilization"] / 100, 1.0) * bar_len)
        bar = "[" + "#" * filled + "-" * (bar_len - filled) + "]"
        status = "HIGH" if s["utilization"] > 70 else "MODERATE" if s["utilization"] > 40 else "LOW"
        lines.append(f"  {i}. {s['name']:<12} {bar} {s['utilization']:>6.1f}% ({status})")
    
    lines.append("")
    
    # Tier 1 professions
    lines.append("-" * 110)
    lines.append("  TIER 1 (PRIMARY >15%) PROFESSIONS BY COUNTRY")
    lines.append("-" * 110)
    lines.append("")
    
    for s in summary_data:
        tier1 = [p for p in s["top_profs"] if p["tier"] == 1]
        if tier1:
            lines.append(f"  {s['name']}:")
            for p in tier1:
                lines.append(f"    - {p['name'][:50]:<50} {p['count']:>10,} ({p['share']*100:.1f}%)")
            lines.append("")
        else:
            lines.append(f"  {s['name']}: No Tier 1 professions (diversified workforce)")
            lines.append("")
    
    # Dominance alerts
    lines.append("-" * 110)
    lines.append("  DOMINANCE ALERTS SUMMARY")
    lines.append("-" * 110)
    lines.append("")
    
    has_alerts = False
    for s in summary_data:
        if s["alerts"]:
            has_alerts = True
            lines.append(f"  {s['name']}:")
            for alert in s["alerts"]:
                icon = {"CRITICAL": "[!!!]", "HIGH": "[!!]", "WATCH": "[!]"}.get(alert["level"], "")
                lines.append(f"    {icon} {alert['level']}: {alert['name'][:40]} - {alert['share']*100:.1f}%")
            lines.append("")
    
    if not has_alerts:
        lines.append("  [OK] No dominance alerts across all QVC countries.")
        lines.append("")
    
    # Recommendations summary
    lines.append("-" * 110)
    lines.append("  CAP RECOMMENDATIONS SUMMARY")
    lines.append("-" * 110)
    lines.append("")
    lines.append(f"  {'Country':<15} {'Current Cap':>15} {'Recommended':>15} {'Change':>15} {'Level':>15}")
    lines.append("  " + "-" * 78)
    
    for s in summary_data:
        change = s["recommended"] - s["cap"]
        lines.append(f"  {s['name']:<15} {s['cap']:>15,} {s['recommended']:>15,} {change:>+15,} {s['rec_level']:>15}")
    
    lines.append("")
    lines.append("=" * 110)
    lines.append("  END OF EXECUTIVE SUMMARY")
    lines.append("=" * 110)
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    print("=" * 80)
    print("QVC COUNTRIES COMPREHENSIVE ANALYSIS")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Data Source: D:\\Quota\\real_data")
    print("=" * 80)
    print()
    
    # Ensure reports directory exists
    REPORT_DIR.mkdir(exist_ok=True)
    
    # Load reference data
    nat_map, prof_map, caps = load_reference_data()
    print()
    
    # Build target codes
    target_codes = set(QVC_COUNTRIES.keys())
    target_codes.update(ALT_CODES.keys())
    # Add versions with leading zeros
    for code in list(QVC_COUNTRIES.keys()):
        target_codes.add(code.zfill(3))
    
    print(f"Target nationality codes: {target_codes}")
    print()
    
    # Analyze workers
    worker_data = analyze_workers(target_codes, prof_map)
    print()
    
    # Generate reports
    all_reports = []
    summary_data = []
    
    for code, name in QVC_COUNTRIES.items():
        print(f"Generating report for {name}...")
        
        # Get data (try different code formats)
        data = worker_data.get(code)
        if not data or data["in_country"] == 0:
            data = worker_data.get(code.zfill(3))
            if data and data["in_country"] > 0:
                code = code.zfill(3)
        
        if not data or data["in_country"] == 0:
            print(f"  [WARN] No data found for {name} (code {code})")
            continue
        
        # Get cap info
        cap_info = caps.get(code) or caps.get(code.zfill(3)) or {"cap_limit": 0, "previous_cap": 0}
        
        # Generate report
        report, summary = generate_country_report(code, name, data, cap_info, prof_map)
        all_reports.append(report)
        summary_data.append(summary)
        
        print(f"  Stock: {summary['stock']:,} | Cap: {summary['cap']:,} | Util: {summary['utilization']:.1f}%")
    
    # Generate executive summary
    print()
    print("Generating executive summary...")
    exec_summary = generate_executive_summary(summary_data)
    
    # Write reports
    print()
    print("Writing reports...")
    
    # Individual reports
    for report, summary in zip(all_reports, summary_data):
        filename = f"qvc_comprehensive_{summary['name'].lower().replace(' ', '_')}_2026.txt"
        filepath = REPORT_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"  Saved: {filename}")
    
    # Combined report
    combined = "\n\n".join(all_reports)
    combined_path = REPORT_DIR / "qvc_comprehensive_all_countries_2026.txt"
    with open(combined_path, "w", encoding="utf-8") as f:
        f.write(combined)
    print(f"  Saved: qvc_comprehensive_all_countries_2026.txt")
    
    # Executive summary
    summary_path = REPORT_DIR / "qvc_comprehensive_executive_summary_2026.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(exec_summary)
    print(f"  Saved: qvc_comprehensive_executive_summary_2026.txt")
    
    # Markdown report
    md_report = generate_markdown_report(summary_data, all_reports)
    md_path = REPORT_DIR / "QVC_Countries_Comprehensive_Analysis_2026.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"  Saved: QVC_Countries_Comprehensive_Analysis_2026.md")
    
    print()
    print("=" * 80)
    print("[OK] All reports generated successfully!")
    print(f"Reports saved to: {REPORT_DIR}")
    print("=" * 80)
    print()
    
    # Print summary to console
    print(exec_summary)


def generate_markdown_report(summary_data: list, all_reports: list) -> str:
    """Generate comprehensive Markdown report."""
    lines = []
    
    lines.append("# QVC Countries Comprehensive Analysis Report 2026")
    lines.append("")
    lines.append(f"**Report Generated:** {datetime.now().strftime('%B %d, %Y')}  ")
    lines.append("**Data Source:** D:\\Quota\\real_data\\07_worker_stock.csv  ")
    lines.append("**Countries Analyzed:** India, Bangladesh, Nepal, Pakistan, Philippines, Sri Lanka")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    
    total_stock = sum(s["stock"] for s in summary_data)
    total_cap = sum(s["cap"] for s in summary_data)
    total_alerts = sum(s["alert_count"] for s in summary_data)
    
    lines.append("### Key Metrics at a Glance")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| **Total Current Stock** | {total_stock:,} |")
    lines.append(f"| **Total Cap Allocation** | {total_cap:,} |")
    lines.append(f"| **Total Headroom** | {total_cap - total_stock:,} |")
    lines.append(f"| **Overall Utilization** | {total_stock/total_cap*100:.1f}% |")
    lines.append(f"| **Active Dominance Alerts** | {total_alerts} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Comparative Analysis
    lines.append("## 1. Comparative Analysis by Country")
    lines.append("")
    lines.append("| Country | Stock | Cap | Headroom | Util % | Growth | Alerts | Rec Cap |")
    lines.append("|---------|-------|-----|----------|--------|--------|--------|---------|")
    
    for s in summary_data:
        alert_str = f"**{s['alert_count']}**" if s['alert_count'] > 0 else "0"
        lines.append(f"| **{s['name']}** | {s['stock']:,} | {s['cap']:,} | {s['headroom']:,} | {s['utilization']:.1f}% | {s['growth_rate']:+.1f}% | {alert_str} | {s['recommended']:,} |")
    
    lines.append(f"| **TOTAL** | **{total_stock:,}** | **{total_cap:,}** | **{total_cap-total_stock:,}** | **{total_stock/total_cap*100:.1f}%** | - | **{total_alerts}** | - |")
    lines.append("")
    
    # Utilization Ranking
    lines.append("### Utilization Ranking")
    lines.append("")
    lines.append("```")
    sorted_by_util = sorted(summary_data, key=lambda x: x["utilization"], reverse=True)
    for i, s in enumerate(sorted_by_util, 1):
        bar_len = 40
        filled = int(min(s["utilization"] / 100, 1.0) * bar_len)
        bar = "#" * filled + "-" * (bar_len - filled)
        status = "HIGH" if s["utilization"] > 70 else "MODERATE" if s["utilization"] > 40 else "LOW"
        lines.append(f"{i}. {s['name']:<12} [{bar}] {s['utilization']:>6.1f}% ({status})")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Tier Classification Overview
    lines.append("## 2. Tier Classification Overview")
    lines.append("")
    lines.append("### Understanding the Tier System")
    lines.append("")
    lines.append("The tier system identifies **demand patterns** for each nationality. Since quotas are limited,")
    lines.append("the system uses tiers to **prioritize allocation**:")
    lines.append("")
    lines.append("- **Tier 1 professions get served FIRST** - These are the highest demand jobs")
    lines.append("- **Lower tiers open only when Tier 1 demand is satisfied**")
    lines.append("- This ensures companies needing the most in-demand workers get priority")
    lines.append("")
    lines.append("**Note:** Dominance alerts (30%+) are a SEPARATE check for concentration risk.")
    lines.append("")
    lines.append("### Tier Definitions")
    lines.append("")
    lines.append("| Tier | Name | Share Range | Description | Allocation Priority |")
    lines.append("|------|------|-------------|-------------|---------------------|")
    lines.append("| **Tier 1** | Primary | > 15% | Highest demand professions - most requested jobs for this nationality | **HIGHEST** - Served first |")
    lines.append("| **Tier 2** | Secondary | 5% - 15% | High demand professions with significant request volume | HIGH - Opens when Tier 1 satisfied |")
    lines.append("| **Tier 3** | Minor | 1% - 5% | Moderate demand professions | MEDIUM - Opens when Tier 1+2 satisfied |")
    lines.append("| **Tier 4** | Unusual | < 1% | Low demand / specialized professions | LOW - Opens when capacity available |")
    lines.append("")
    
    # Tier 1 professions
    lines.append("### Tier 1 (Primary) Professions by Country - HIGHEST DEMAND JOBS")
    lines.append("")
    lines.append("These are the **highest demand professions** for each nationality. Companies requesting these jobs get **priority allocation**.")
    lines.append("")
    lines.append("| Country | Profession | Workers | Share % | Allocation Priority | Dominance Status |")
    lines.append("|---------|------------|---------|---------|---------------------|------------------|")
    
    has_tier1 = False
    for s in summary_data:
        tier1 = [p for p in s["top_profs"] if p["tier"] == 1]
        if tier1:
            has_tier1 = True
            for p in tier1:
                dom_status = "WATCH (>30%)" if p["share"] >= 0.30 else "OK"
                lines.append(f"| **{s['name']}** | {p['name'][:30]} | {p['count']:,} | **{p['share']*100:.1f}%** | **HIGHEST** | {dom_status} |")
        else:
            lines.append(f"| {s['name']} | *No single profession >15%* | - | - | Distributed | *Diversified* |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Individual Country Analysis
    lines.append("## 3. Individual Country Analysis")
    lines.append("")
    
    for s in summary_data:
        lines.append(f"### {s['name'].upper()}")
        lines.append("")
        lines.append("#### Key Performance Indicators")
        lines.append("")
        lines.append("| Metric | Value | Status |")
        lines.append("|--------|-------|--------|")
        lines.append(f"| Current Stock | {s['stock']:,} | In-Country Workers |")
        lines.append(f"| Cap (2026) | {s['cap']:,} | Policy Limit |")
        lines.append(f"| Headroom | {s['headroom']:,} | Available Capacity |")
        lines.append(f"| Utilization | **{s['utilization']:.1f}%** | {'HIGH' if s['utilization'] > 70 else 'MODERATE' if s['utilization'] > 40 else 'LOW'} |")
        lines.append(f"| Professions | {s['num_professions']:,} | Diversity Index |")
        lines.append(f"| Growth Rate | {s['growth_rate']:+.1f}% | 6-Month Trend |")
        lines.append("")
        
        # Utilization bar
        util_bar_len = 40
        filled = int(min(s["utilization"] / 100, 1.0) * util_bar_len)
        bar = "#" * filled + "-" * (util_bar_len - filled)
        lines.append("#### Utilization")
        lines.append(f"```")
        lines.append(f"[{bar}] {s['utilization']:.1f}%")
        lines.append("```")
        lines.append("")
        
        # Tier distribution
        lines.append("#### Tier Distribution")
        lines.append("")
        lines.append("| Tier | Workers | Share % |")
        lines.append("|------|---------|---------|")
        for tier in [1, 2, 3, 4]:
            tier_names = {1: "Tier 1 (Highest Demand)", 2: "Tier 2 (High Demand)", 3: "Tier 3 (Moderate)", 4: "Tier 4 (Low/Specialized)"}
            tier_count = s["tier_totals"].get(tier, 0)
            tier_share = tier_count / s["stock"] * 100 if s["stock"] > 0 else 0
            lines.append(f"| {tier_names[tier]} | {tier_count:,} | {tier_share:.1f}% |")
        lines.append("")
        
        # Top 10 professions
        lines.append("#### Top 10 Professions")
        lines.append("")
        lines.append("| # | Profession | Tier | Workers | Share % |")
        lines.append("|---|------------|------|---------|---------|")
        for i, p in enumerate(s["top_profs"][:10], 1):
            lines.append(f"| {i} | {p['name'][:35]} | T{p['tier']} | {p['count']:,} | {p['share']*100:.1f}% |")
        lines.append("")
        
        # Dominance assessment
        lines.append("#### Dominance Risk Assessment")
        if s["alerts"]:
            for alert in s["alerts"]:
                lines.append(f"")
                lines.append(f"> **{alert['level']} ALERT**")
                lines.append(f"> ")
                lines.append(f"> **Profession:** {alert['name']}  ")
                lines.append(f"> **Share:** {alert['share']*100:.1f}%  ")
                lines.append(f"> **Status:** Exceeds {30 if alert['level'] == 'WATCH' else 40 if alert['level'] == 'HIGH' else 50}% threshold  ")
        else:
            lines.append("**Status:** No active alerts  ")
            lines.append("All professions are below the 30% concentration threshold.")
        lines.append("")
        
        # Cap recommendation
        lines.append("#### Cap Recommendation")
        lines.append(f"- **Current Cap:** {s['cap']:,}")
        lines.append(f"- **Recommended:** {s['recommended']:,} ({s['rec_level']})")
        lines.append(f"- **Change:** {s['recommended'] - s['cap']:+,}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Dominance Alerts Summary
    lines.append("## 4. Dominance Alerts Summary")
    lines.append("")
    
    has_alerts = any(s["alerts"] for s in summary_data)
    if has_alerts:
        lines.append("### Active Alerts")
        lines.append("")
        lines.append("| Country | Profession | Share % | Alert Level | Action |")
        lines.append("|---------|------------|---------|-------------|--------|")
        
        for s in summary_data:
            for alert in s["alerts"]:
                lines.append(f"| **{s['name']}** | {alert['name'][:30]} | **{alert['share']*100:.1f}%** | {alert['level']} | Monitor closely |")
        
        lines.append("")
    else:
        lines.append("**[OK] No active dominance alerts across all QVC countries.**")
        lines.append("")
    
    lines.append("### Alert Thresholds Reference")
    lines.append("")
    lines.append("| Level | Threshold | Action |")
    lines.append("|-------|-----------|--------|")
    lines.append("| **WATCH** | 30% - 39% | Monitor trends, consider diversification |")
    lines.append("| **HIGH** | 40% - 49% | Active intervention recommended |")
    lines.append("| **CRITICAL** | 50%+ | Blocking new approvals in that profession |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Cap Recommendations Summary
    lines.append("## 5. Cap Recommendations Summary")
    lines.append("")
    lines.append("| Country | Current Cap | Recommended | Change | Level |")
    lines.append("|---------|-------------|-------------|--------|-------|")
    
    total_current = 0
    total_recommended = 0
    
    for s in summary_data:
        change = s["recommended"] - s["cap"]
        total_current += s["cap"]
        total_recommended += s["recommended"]
        lines.append(f"| **{s['name']}** | {s['cap']:,} | {s['recommended']:,} | {change:+,} | {s['rec_level']} |")
    
    lines.append(f"| **TOTAL** | **{total_current:,}** | **{total_recommended:,}** | **{total_recommended - total_current:+,}** | - |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Key Insights
    lines.append("## 6. Key Insights & Recommendations")
    lines.append("")
    
    # Find highest/lowest utilization
    highest_util = max(summary_data, key=lambda x: x["utilization"])
    lowest_util = min(summary_data, key=lambda x: x["utilization"])
    
    lines.append("### High Performers")
    lines.append("")
    lines.append(f"1. **{highest_util['name']}** - Highest utilization at {highest_util['utilization']:.1f}%")
    lines.append(f"   - Strong workforce demand")
    lines.append(f"   - Headroom: {highest_util['headroom']:,}")
    lines.append("")
    
    lines.append("### Areas for Attention")
    lines.append("")
    lines.append(f"1. **{lowest_util['name']}** - Lowest utilization at {lowest_util['utilization']:.1f}%")
    lines.append(f"   - {lowest_util['headroom']:,} unused capacity")
    lines.append(f"   - **Recommendation:** Review allocation methodology or demand patterns")
    lines.append("")
    
    # Diversification status
    lines.append("### Diversification Status")
    lines.append("")
    lines.append("| Status | Countries |")
    lines.append("|--------|-----------|")
    
    diversified = [s["name"] for s in summary_data if not any(p["tier"] == 1 for p in s["top_profs"])]
    moderate = [s["name"] for s in summary_data if any(p["tier"] == 1 and p["share"] < 0.30 for p in s["top_profs"])]
    alert = [s["name"] for s in summary_data if any(p["tier"] == 1 and p["share"] >= 0.30 for p in s["top_profs"])]
    
    lines.append(f"| **Fully Diversified** (No Tier 1) | {', '.join(diversified) if diversified else 'None'} |")
    lines.append(f"| **Moderately Concentrated** (Tier 1 < 30%) | {', '.join(moderate) if moderate else 'None'} |")
    lines.append(f"| **Concentration Alert** (Tier 1 >= 30%) | {', '.join(alert) if alert else 'None'} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Appendix
    lines.append("## Appendix A: Methodology")
    lines.append("")
    lines.append("### Tier Classification")
    lines.append("")
    lines.append("Professions are classified into tiers based on their share of total workforce, representing **demand patterns**:")
    lines.append("")
    lines.append("- **Tier 1 (Primary):** Share >= 15% - Highest demand jobs, get **priority allocation**")
    lines.append("- **Tier 2 (Secondary):** Share >= 5% and < 15% - High demand, opens when Tier 1 demand satisfied")
    lines.append("- **Tier 3 (Minor):** Share >= 1% and < 5% - Moderate demand")
    lines.append("- **Tier 4 (Unusual):** Share < 1% - Low demand / specialized roles")
    lines.append("")
    lines.append("**Key Principle:** Since nationality quotas are limited, the system prioritizes Tier 1 professions first,")
    lines.append("ensuring companies requesting high-demand jobs get served before lower tiers open.")
    lines.append("")
    lines.append("### Cap Recommendation Algorithm")
    lines.append("")
    lines.append("The AI recommendation engine considers:")
    lines.append("- Current utilization rate")
    lines.append("- Number of active dominance alerts")
    lines.append("- Growth trend (6-month)")
    lines.append("- Workforce diversification")
    lines.append("")
    lines.append("### Data Source")
    lines.append("")
    lines.append("- **File:** D:\\Quota\\real_data\\07_worker_stock.csv")
    lines.append("- **Reference:** 01_nationalities.csv, 02_professions.csv, 05_nationality_caps.csv")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*End of Report*")
    
    return "\n".join(lines)


if __name__ == "__main__":
    main()
