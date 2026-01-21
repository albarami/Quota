#!/usr/bin/env python
"""
Real data analysis script for nationality quota report.

Analyzes ministry data to generate reports for restricted nationalities:
- Current stock (workers in country)
- Top tier occupations
- Expected growth
- Recommended cap

Usage:
    python scripts/analyze_real_data.py
"""

import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Data directory
DATA_DIR = Path(__file__).parent.parent / "real_data"

# Target nationalities (ISO numeric codes)
TARGET_NATIONALITIES = {
    "818": "Egypt",
    "886": "Yemen", 
    "760": "Syria",
    "368": "Iraq",
    "004": "Afghanistan",  # Also check "4"
}

# Alternative codes (some may be stored without leading zeros)
ALT_CODES = {
    "4": "Afghanistan",
}


def load_csv(filename: str) -> list[dict]:
    """Load CSV file and return list of dictionaries."""
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


def load_nationalities() -> dict:
    """Load nationality code to name mapping."""
    rows = load_csv("01_nationalities.csv")
    nat_map = {}
    for row in rows:
        code = row.get("code", "").strip()
        name = row.get("name", "").strip()
        if code and name:
            nat_map[code] = name
    return nat_map


def load_professions() -> dict:
    """Load profession code to name mapping."""
    rows = load_csv("02_professions.csv")
    prof_map = {}
    for row in rows:
        code = row.get("code", "").strip()
        name = row.get("name", "").strip()
        if code and name:
            prof_map[code] = name
    return prof_map


def load_caps() -> dict:
    """Load nationality caps."""
    rows = load_csv("05_nationality_caps.csv")
    caps = {}
    for row in rows:
        code = row.get("nationality_code", "").strip().strip('"')
        cap_limit = row.get("cap_limit", "0")
        previous_cap = row.get("previous_cap", "0")
        try:
            caps[code] = {
                "cap_limit": int(cap_limit),
                "previous_cap": int(previous_cap),
            }
        except ValueError:
            pass
    return caps


def analyze_workers(target_codes: set, prof_map: dict) -> dict:
    """Analyze worker stock for target nationalities."""
    print("Loading worker data (this may take a moment)...")
    
    # Initialize results
    results = defaultdict(lambda: {
        "in_country": 0,
        "out_country": 0,
        "committed": 0,
        "pending": 0,
        "total": 0,
        "professions": defaultdict(int),
        "recent_entries": 0,  # Last 6 months
        "recent_exits": 0,    # Last 6 months
    })
    
    filepath = DATA_DIR / "07_worker_stock.csv"
    if not filepath.exists():
        print(f"[ERROR] Worker file not found: {filepath}")
        return results
    
    # Calculate date 6 months ago
    six_months_ago = datetime.now() - timedelta(days=180)
    
    row_count = 0
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_count += 1
            if row_count % 100000 == 0:
                print(f"  Processing row {row_count:,}...")
            
            nat_code = row.get("nationality_code", "").strip().strip('"')
            
            # Check if this is a target nationality
            if nat_code not in target_codes:
                continue
            
            state = row.get("state", "").strip().upper()
            prof_code = row.get("profession_code", "").strip().strip('"')
            
            # Count by state
            if state == "IN_COUNTRY":
                results[nat_code]["in_country"] += 1
                results[nat_code]["professions"][prof_code] += 1
            elif state == "OUT_COUNTRY":
                results[nat_code]["out_country"] += 1
            elif state == "COMMITTED":
                results[nat_code]["committed"] += 1
            elif state == "PENDING":
                results[nat_code]["pending"] += 1
            
            results[nat_code]["total"] += 1
            
            # Check recent employment dates for growth analysis
            emp_start = row.get("employment_start", "")
            emp_end = row.get("employment_end", "")
            
            try:
                if emp_start:
                    start_date = datetime.strptime(emp_start[:10], "%Y-%m-%d")
                    if start_date >= six_months_ago:
                        results[nat_code]["recent_entries"] += 1
            except (ValueError, TypeError):
                pass
            
            try:
                if emp_end:
                    end_date = datetime.strptime(emp_end[:10], "%Y-%m-%d")
                    if end_date >= six_months_ago:
                        results[nat_code]["recent_exits"] += 1
            except (ValueError, TypeError):
                pass
    
    print(f"  Processed {row_count:,} total rows")
    return results


def calculate_tier(share_pct: float) -> int:
    """Calculate tier level based on share percentage."""
    if share_pct >= 0.15:
        return 1  # Primary: >15%
    elif share_pct >= 0.05:
        return 2  # Secondary: 5-15%
    elif share_pct >= 0.01:
        return 3  # Minor: 1-5%
    else:
        return 4  # Unusual: <1%


def get_top_professions(professions: dict, prof_map: dict, total: int, top_n: int = 10) -> list:
    """Get top N professions with tier classification."""
    if total == 0:
        return []
    
    # Sort by count
    sorted_profs = sorted(professions.items(), key=lambda x: x[1], reverse=True)
    
    results = []
    for prof_code, count in sorted_profs[:top_n]:
        share = count / total
        tier = calculate_tier(share)
        prof_name = prof_map.get(prof_code, f"Unknown ({prof_code})")
        results.append({
            "code": prof_code,
            "name": prof_name,
            "count": count,
            "share": share,
            "tier": tier,
        })
    
    return results


def calculate_recommended_cap(current_stock: int, growth_rate: float, cap_limit: int) -> dict:
    """Calculate recommended cap based on growth analysis."""
    # Project 12-month growth based on 6-month trend
    projected_growth = int(current_stock * growth_rate * 2)
    projected_stock = current_stock + projected_growth
    
    # Calculate headroom
    current_headroom = cap_limit - current_stock
    headroom_pct = (current_headroom / cap_limit * 100) if cap_limit > 0 else 0
    
    # Recommendation logic
    if headroom_pct < 5:
        recommendation = "INCREASE"
        suggested_cap = int(projected_stock * 1.15)  # 15% buffer
    elif headroom_pct < 15:
        recommendation = "MAINTAIN"
        suggested_cap = cap_limit
    elif headroom_pct > 30:
        recommendation = "DECREASE"
        suggested_cap = int(projected_stock * 1.10)  # 10% buffer
    else:
        recommendation = "MAINTAIN"
        suggested_cap = cap_limit
    
    return {
        "current_headroom": current_headroom,
        "headroom_pct": headroom_pct,
        "projected_growth": projected_growth,
        "projected_stock": projected_stock,
        "recommendation": recommendation,
        "suggested_cap": suggested_cap,
    }


def generate_report():
    """Generate comprehensive report for target nationalities."""
    print("=" * 70)
    print("NATIONALITY QUOTA ANALYSIS REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    # Load reference data
    print("Loading reference data...")
    nat_map = load_nationalities()
    prof_map = load_professions()
    caps = load_caps()
    
    print(f"  Loaded {len(nat_map)} nationalities")
    print(f"  Loaded {len(prof_map)} professions")
    print(f"  Loaded {len(caps)} caps")
    print()
    
    # Build target codes set (including alternatives)
    target_codes = set(TARGET_NATIONALITIES.keys())
    target_codes.update(ALT_CODES.keys())
    
    # Analyze workers
    worker_data = analyze_workers(target_codes, prof_map)
    print()
    
    # Generate report for each nationality
    report_data = []
    
    for code, name in TARGET_NATIONALITIES.items():
        # Check for alternative code
        data = worker_data.get(code)
        if not data or data["in_country"] == 0:
            # Try without leading zeros
            alt_code = code.lstrip("0")
            data = worker_data.get(alt_code)
            if data:
                code = alt_code
        
        if not data:
            print(f"[WARN] No data found for {name} (code: {code})")
            continue
        
        # Get cap info
        cap_info = caps.get(code) or caps.get(code.zfill(3)) or {"cap_limit": 0, "previous_cap": 0}
        
        # Calculate growth rate (6-month)
        net_change = data["recent_entries"] - data["recent_exits"]
        growth_rate = net_change / data["in_country"] if data["in_country"] > 0 else 0
        
        # Calculate cap recommendation
        cap_rec = calculate_recommended_cap(
            data["in_country"],
            growth_rate,
            cap_info["cap_limit"]
        )
        
        # Get top professions
        top_profs = get_top_professions(data["professions"], prof_map, data["in_country"])
        
        report_data.append({
            "code": code,
            "name": name,
            "data": data,
            "cap_info": cap_info,
            "growth_rate": growth_rate,
            "cap_rec": cap_rec,
            "top_profs": top_profs,
        })
    
    # Print reports
    for entry in report_data:
        print_nationality_report(entry)
    
    # Print summary table
    print_summary_table(report_data)
    
    return report_data


def print_nationality_report(entry: dict):
    """Print detailed report for a nationality."""
    name = entry["name"]
    data = entry["data"]
    cap_info = entry["cap_info"]
    growth_rate = entry["growth_rate"]
    cap_rec = entry["cap_rec"]
    top_profs = entry["top_profs"]
    
    print("=" * 70)
    print(f"  {name.upper()} (Code: {entry['code']})")
    print("=" * 70)
    print()
    
    # Current Stock
    print("CURRENT STOCK:")
    print(f"  In Country:     {data['in_country']:>12,}")
    print(f"  Out of Country: {data['out_country']:>12,}")
    print(f"  Committed:      {data['committed']:>12,}")
    print(f"  Pending:        {data['pending']:>12,}")
    print(f"  -----------------------------")
    print(f"  TOTAL RECORDS:  {data['total']:>12,}")
    print()
    
    # Cap Information
    print("CAP INFORMATION:")
    print(f"  Current Cap (2026):    {cap_info['cap_limit']:>12,}")
    print(f"  Previous Cap (2025):   {cap_info['previous_cap']:>12,}")
    print(f"  Current Stock:         {data['in_country']:>12,}")
    print(f"  Available Headroom:    {cap_rec['current_headroom']:>12,}")
    print(f"  Utilization:           {(data['in_country']/cap_info['cap_limit']*100 if cap_info['cap_limit'] > 0 else 0):>11.1f}%")
    print()
    
    # Growth Analysis
    print("GROWTH ANALYSIS (6-month period):")
    print(f"  Recent Entries:        {data['recent_entries']:>12,}")
    print(f"  Recent Exits:          {data['recent_exits']:>12,}")
    print(f"  Net Change:            {data['recent_entries'] - data['recent_exits']:>+12,}")
    print(f"  Growth Rate:           {growth_rate*100:>11.2f}%")
    print(f"  Projected Annual:      {cap_rec['projected_growth']:>+12,}")
    print(f"  Projected Stock (12m): {cap_rec['projected_stock']:>12,}")
    print()
    
    # Cap Recommendation
    print("CAP RECOMMENDATION:")
    print(f"  Status:                {cap_rec['recommendation']:>12}")
    print(f"  Suggested Cap:         {cap_rec['suggested_cap']:>12,}")
    cap_change = cap_rec['suggested_cap'] - cap_info['cap_limit']
    print(f"  Change from Current:   {cap_change:>+12,}")
    print()
    
    # Top Professions (Tier Analysis)
    print("TOP 10 PROFESSIONS (TIER CLASSIFICATION):")
    print("  " + "-" * 65)
    print(f"  {'Tier':<6} {'Profession':<35} {'Count':>10} {'Share':>8}")
    print("  " + "-" * 65)
    
    for prof in top_profs:
        tier_label = f"T{prof['tier']}"
        prof_name = prof['name'][:33] if len(prof['name']) > 33 else prof['name']
        print(f"  {tier_label:<6} {prof_name:<35} {prof['count']:>10,} {prof['share']*100:>7.1f}%")
    
    # Tier summary
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for prof in top_profs:
        tier_counts[prof['tier']] += prof['count']
    
    print("  " + "-" * 65)
    print()
    print("  TIER SUMMARY (Top 10 only):")
    print(f"    Tier 1 (Primary >15%):    {tier_counts[1]:>10,}")
    print(f"    Tier 2 (Secondary 5-15%): {tier_counts[2]:>10,}")
    print(f"    Tier 3 (Minor 1-5%):      {tier_counts[3]:>10,}")
    print(f"    Tier 4 (Unusual <1%):     {tier_counts[4]:>10,}")
    print()
    print()


def print_summary_table(report_data: list):
    """Print summary comparison table."""
    print("=" * 70)
    print("  SUMMARY COMPARISON TABLE")
    print("=" * 70)
    print()
    print(f"{'Nationality':<15} {'Stock':>10} {'Cap':>10} {'Headroom':>10} {'Util%':>8} {'Rec':>12} {'Suggested':>12}")
    print("-" * 70)
    
    for entry in report_data:
        name = entry["name"][:13]
        stock = entry["data"]["in_country"]
        cap = entry["cap_info"]["cap_limit"]
        headroom = entry["cap_rec"]["current_headroom"]
        util = (stock / cap * 100) if cap > 0 else 0
        rec = entry["cap_rec"]["recommendation"]
        suggested = entry["cap_rec"]["suggested_cap"]
        
        print(f"{name:<15} {stock:>10,} {cap:>10,} {headroom:>10,} {util:>7.1f}% {rec:>12} {suggested:>12,}")
    
    print("-" * 70)
    print()
    
    # Tier 1 occupations comparison
    print("TOP TIER 1 OCCUPATIONS BY NATIONALITY:")
    print("-" * 70)
    for entry in report_data:
        name = entry["name"]
        tier1_profs = [p for p in entry["top_profs"] if p["tier"] == 1]
        if tier1_profs:
            print(f"\n{name}:")
            for p in tier1_profs:
                print(f"  - {p['name'][:40]}: {p['count']:,} ({p['share']*100:.1f}%)")
    
    print()


if __name__ == "__main__":
    report_data = generate_report()
