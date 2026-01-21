"""
Live Dashboard Page.

Real-time monitoring of nationality quotas, tiers, and alerts.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import requests
from datetime import datetime

from app.components.styles import apply_custom_css, render_header, render_gold_accent
from app.components.charts import (
    create_headroom_gauge,
    create_tier_bar_chart,
)
from app.components.tables import render_tier_table, render_alerts_table
from app.components.cards import (
    render_metric_card,
    render_tier_card,
    render_alert_card,
    render_kpi_row,
    render_utilization_bar,
)


st.set_page_config(
    page_title="Dashboard | Qatar Quota System",
    page_icon="📊",
    layout="wide",
)

apply_custom_css()

# Header
render_header(
    "Live Dashboard",
    "Real-time monitoring of nationality quotas and system status"
)

# API base URL
API_BASE = st.session_state.get("api_base_url", "http://localhost:8000")

# Nationality selector
st.markdown("### Select Nationality")
render_gold_accent()

# Restricted nationalities (matching database)
NATIONALITIES = {
    "EGY": "Egypt",
    "IND": "India",
    "PAK": "Pakistan",
    "NPL": "Nepal",
    "BGD": "Bangladesh",
    "PHL": "Philippines",
    "LKA": "Sri Lanka",
    "IRN": "Iran",
    "IRQ": "Iraq",
    "YEM": "Yemen",
    "SYR": "Syria",
    "AFG": "Afghanistan",
}

selected_code = st.selectbox(
    "Nationality",
    options=list(NATIONALITIES.keys()),
    format_func=lambda x: f"{x} - {NATIONALITIES[x]}",
    label_visibility="collapsed",
)


def fetch_dashboard_data(nationality_code: str):
    """
    Fetch dashboard data - tries real data first, then API, then demo data.
    """
    # Try real data from CSV files first (priority)
    try:
        from app.utils.real_data_loader import get_real_dashboard_data, check_real_data_available
        if check_real_data_available():
            data = get_real_dashboard_data(nationality_code)
            if data and data.get("stock", 0) > 0:
                return data
    except Exception as e:
        print(f"Real data load error: {e}")
    
    # Try API second (for local development with FastAPI running)
    try:
        response = requests.get(
            f"{API_BASE}/api/v1/dashboard/{nationality_code}",
            timeout=2  # Short timeout
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass  # API not available, try database
    
    # Try direct database query (for Streamlit Cloud)
    try:
        from app.utils.db_queries import get_dashboard_data as db_get_dashboard
        data = db_get_dashboard(nationality_code)
        if data and data.get("nationality_id"):
            return data
    except Exception:
        pass  # Database not available, use demo
    
    # Fallback to realistic demo data that varies by nationality
    return _generate_demo_data(nationality_code)


def _generate_demo_data(nationality_code: str) -> dict:
    """Generate realistic demo data that varies by nationality."""
    import hashlib
    
    # Use nationality code to generate consistent but varying numbers
    seed = int(hashlib.md5(nationality_code.encode()).hexdigest()[:8], 16)
    
    # Realistic data ranges per nationality (from worker_stock.csv real data)
    # NOTE: tier1_status is based on UTILIZATION, not dominance alerts
    demo_profiles = {
        # All data from real ministry worker_stock.csv - EXACT VALUES
        "EGY": {"cap": 81668, "stock": 71574, "tier1_status": "OPEN"},       # 87.6% util
        "YEM": {"cap": 14949, "stock": 13105, "tier1_status": "OPEN"},       # 87.7% util, NO dominance alerts
        "SYR": {"cap": 27038, "stock": 23324, "tier1_status": "OPEN"},       # 86.3% util
        "IRQ": {"cap": 1959, "stock": 1658, "tier1_status": "OPEN"},         # 84.6% util
        "AFG": {"cap": 3016, "stock": 2532, "tier1_status": "OPEN"},         # 84.0% util
        "IRN": {"cap": 7768, "stock": 6683, "tier1_status": "OPEN"},         # 86.0% util
        # QVC countries - EXACT VALUES from worker_stock.csv
        "BGD": {"cap": 487741, "stock": 400273, "tier1_status": "OPEN"},     # 82.1% util
        "PAK": {"cap": 242955, "stock": 196277, "tier1_status": "OPEN"},     # 80.8% util
        "NPL": {"cap": 437178, "stock": 346515, "tier1_status": "RATIONED"}, # 79.3% util
        "IND": {"cap": 676569, "stock": 529575, "tier1_status": "OPEN"},     # 78.3% util
        "LKA": {"cap": 136111, "stock": 101272, "tier1_status": "OPEN"},     # 74.4% util
        "PHL": {"cap": 155806, "stock": 126653, "tier1_status": "OPEN"},     # 81.3% util
    }
    
    profile = demo_profiles.get(nationality_code, {
        "cap": 15000 + (seed % 10000),
        "stock": 12000 + (seed % 8000),
        "tier1_status": "OPEN"
    })
    
    cap = profile["cap"]
    stock = profile["stock"]
    
    # Effective Headroom Formula (Section 5, Section 11.B):
    # headroom = cap - stock - committed - (pending × 0.8) + (outflow × 0.75)
    # For demo data, we estimate committed=0, pending=0, outflow=1.5% of stock monthly
    committed = 0  # Demo: no committed workers in pipeline
    pending = 0    # Demo: no pending requests
    projected_outflow = int(stock * 0.015)  # ~1.5% monthly outflow estimate
    
    # Full headroom calculation per documentation
    headroom = cap - stock - committed - int(pending * 0.8) + int(projected_outflow * 0.75)
    headroom = max(0, headroom)  # Cannot be negative
    
    utilization = stock / cap if cap > 0 else 0
    
    # Vary tier capacities based on headroom
    t1_cap = int(headroom * 0.45)
    t2_cap = int(headroom * 0.30)
    t3_cap = int(headroom * 0.15)
    t4_cap = int(headroom * 0.10)
    
    # Determine tier statuses based on utilization
    if utilization > 0.92:
        tier_statuses = [
            {"tier_level": 1, "tier_name": "Primary", "status": "LIMITED", "capacity": t1_cap, "share_pct": 0.35},
            {"tier_level": 2, "tier_name": "Secondary", "status": "CLOSED", "capacity": 0, "share_pct": 0.10},
            {"tier_level": 3, "tier_name": "Minor", "status": "CLOSED", "capacity": 0, "share_pct": 0.03},
            {"tier_level": 4, "tier_name": "Unusual", "status": "CLOSED", "capacity": 0, "share_pct": 0.01},
        ]
    elif utilization > 0.85:
        tier_statuses = [
            {"tier_level": 1, "tier_name": "Primary", "status": profile["tier1_status"], "capacity": t1_cap, "share_pct": 0.32},
            {"tier_level": 2, "tier_name": "Secondary", "status": "RATIONED", "capacity": t2_cap, "share_pct": 0.11},
            {"tier_level": 3, "tier_name": "Minor", "status": "LIMITED", "capacity": t3_cap, "share_pct": 0.04},
            {"tier_level": 4, "tier_name": "Unusual", "status": "CLOSED", "capacity": 0, "share_pct": 0.01},
        ]
    else:
        tier_statuses = [
            {"tier_level": 1, "tier_name": "Primary", "status": "OPEN", "capacity": t1_cap, "share_pct": 0.28},
            {"tier_level": 2, "tier_name": "Secondary", "status": "OPEN", "capacity": t2_cap, "share_pct": 0.09},
            {"tier_level": 3, "tier_name": "Minor", "status": "RATIONED", "capacity": t3_cap, "share_pct": 0.03},
            {"tier_level": 4, "tier_name": "Unusual", "status": "LIMITED", "capacity": t4_cap, "share_pct": 0.01},
        ]
    
    # ================================================================
    # DOMINANCE ALERTS (Section 6, Section 11.D)
    # Formula: Dominance_Share = Nationality_Workers_in_Profession / Total_Workers_in_Profession
    # Thresholds: WATCH >= 30%, HIGH >= 40%, CRITICAL >= 50%
    # Only applies to professions with >= 200 total workers (MIN_PROFESSION_SIZE)
    # ================================================================
    
    # Demo dominance alerts based on CORRECT formula from real data
    # Formula: Dominance = Nationality_Workers / Total_Workers_in_Profession
    # NOT: Tier_Share = Profession_Workers / Total_Nationality_Workers
    # Format: (profession_name, dominance_share, velocity, alert_level, nat_workers, total_workers)
    demo_dominance_alerts = {
        # NOTE: Yemen has NO dominance alerts - EMPLOYEE is 6,741/59,202 = 11.4% (below 30%)
        # The 51.4% was the TIER share (wrong metric), not DOMINANCE share (correct)
        "BGD": [
            # Bangladesh: High dominance in specialized professions
            ("STRUCT DRAFTSMAN", 0.937, 0.02, "CRITICAL", 1150, 1227),
        ],
        "IND": [
            # India: High dominance in technical professions
            ("METAL POUR TECH", 0.792, 0.02, "CRITICAL", 494, 624),
        ],
        "EGY": [
            # Egypt: Legal profession dominance
            ("LEGAL PROFESSIONAL", 0.508, 0.02, "CRITICAL", 302, 595),
        ],
        "NPL": [
            # Nepal: Specialized professions
            ("GENTS' TAILOR", 0.517, 0.02, "CRITICAL", 593, 1146),
        ],
        "PAK": [
            # Pakistan: Security profession dominance
            ("POLICE ARMY STAFF", 0.559, 0.02, "CRITICAL", 4478, 8018),
        ],
        "PHL": [
            # Philippines: Healthcare dominance
            ("Care Giver", 0.887, 0.02, "CRITICAL", 1369, 1544),
        ],
        "LKA": [
            # Sri Lanka: Technical profession
            ("QUANT CALCUL TECH", 0.347, 0.02, "WATCH", 242, 697),
        ],
    }
    
    # Get nationality-specific alerts or generate generic ones
    alerts = []
    if nationality_code in demo_dominance_alerts:
        for prof_name, share, vel, level, nat_w, total_w in demo_dominance_alerts[nationality_code]:
            alerts.append({
                "profession_id": hash(prof_name) % 10000,
                "profession_name": prof_name,
                "share_pct": share,
                "nationality_workers": nat_w,
                "total_in_profession": total_w,
                "velocity": vel,
                "alert_level": level,
                "is_blocking": level == "CRITICAL",
            })
    else:
        # No dominance alerts for this nationality (most have none)
        alerts = []
    
    # Queue counts vary by utilization
    queue_multiplier = 1 + (utilization * 2)
    queue_counts = {
        1: int(35 * queue_multiplier + (seed % 30)),
        2: int(65 * queue_multiplier + (seed % 50)),
        3: int(15 * queue_multiplier + (seed % 20)),
        4: int(5 * queue_multiplier + (seed % 10)),
    }
    
    # Growth rates calculated from actual 2024-2025 worker movement data
    # Formula: (Joined_2025 - Left_2025) / Stock_End_2024 × 100
    GROWTH_RATES = {
        'BGD': +0.92,   # Bangladesh: GROWING +3,649 workers
        'PAK': +0.74,   # Pakistan: GROWING +1,443 workers
        'YEM': -1.26,   # Yemen: -167 workers
        'IRQ': -6.38,   # Iraq: -113 workers
        'IRN': -6.79,   # Iran: -487 workers
        'NPL': -9.17,   # Nepal: -34,980 workers
        'AFG': -9.47,   # Afghanistan: -265 workers
        'EGY': -10.79,  # Egypt: -8,661 workers
        'IND': -11.95,  # India: -71,868 workers
        'SYR': -12.37,  # Syria: -3,291 workers
        'PHL': -13.34,  # Philippines: -19,490 workers
        'LKA': -17.39,  # Sri Lanka: -21,317 workers
    }
    growth_rate = GROWTH_RATES.get(nationality_code, 0)
    
    return {
        "nationality_id": list(NATIONALITIES.keys()).index(nationality_code) + 1 if nationality_code in NATIONALITIES else 1,
        "nationality_code": nationality_code,
        "nationality_name": NATIONALITIES.get(nationality_code, nationality_code),
        "cap": cap,
        "stock": stock,
        "headroom": headroom,
        "utilization_pct": utilization,
        "tier_statuses": tier_statuses,
        "dominance_alerts": alerts,
        "queue_counts": queue_counts,
        "projected_outflow": int(stock * 0.015),  # ~1.5% monthly outflow
        "growth_rate": growth_rate,
        "last_updated": datetime.now().isoformat(),
    }


# Fetch data
data = fetch_dashboard_data(selected_code)

# KPI Row
st.markdown("<br>", unsafe_allow_html=True)
kpi_cols = st.columns(4)

with kpi_cols[0]:
    render_metric_card(
        label="Annual Cap",
        value=data["cap"],
        icon="🎯"
    )

with kpi_cols[1]:
    render_metric_card(
        label="Current Stock",
        value=data["stock"],
        delta=f"{data['utilization_pct']:.1%} utilized",
        icon="👥"
    )

with kpi_cols[2]:
    render_metric_card(
        label="Effective Headroom",
        value=data["headroom"],
        icon="📈"
    )

with kpi_cols[3]:
    growth = data.get("growth_rate", 0)
    growth_text = f"{growth:+.1f}%"
    growth_status = "Growing" if growth > 0 else "Declining" if growth < 0 else "Stable"
    render_metric_card(
        label="YoY Growth Rate",
        value=growth_text,
        delta=growth_status,
        icon="📊"
    )

st.markdown("<br>", unsafe_allow_html=True)

# Utilization bar
render_utilization_bar(
    current=data["stock"],
    maximum=data["cap"],
    label=f"{data['nationality_code']} Cap Utilization"
)

st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)

# Two columns: Tier Status and Alerts
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Tier Status")
    render_gold_accent()
    
    # Tier cards in 2x2 grid
    tier_row1 = st.columns(2)
    tier_row2 = st.columns(2)
    
    tiers = data["tier_statuses"]
    
    with tier_row1[0]:
        t = tiers[0]
        render_tier_card(
            tier_level=t["tier_level"],
            tier_name=t["tier_name"],
            status=t["status"],
            capacity=t["capacity"],
            share_pct=t.get("share_pct"),
        )
    
    with tier_row1[1]:
        t = tiers[1]
        render_tier_card(
            tier_level=t["tier_level"],
            tier_name=t["tier_name"],
            status=t["status"],
            capacity=t["capacity"],
            share_pct=t.get("share_pct"),
        )
    
    with tier_row2[0]:
        t = tiers[2]
        render_tier_card(
            tier_level=t["tier_level"],
            tier_name=t["tier_name"],
            status=t["status"],
            capacity=t["capacity"],
            share_pct=t.get("share_pct"),
        )
    
    with tier_row2[1]:
        t = tiers[3]
        render_tier_card(
            tier_level=t["tier_level"],
            tier_name=t["tier_name"],
            status=t["status"],
            capacity=t["capacity"],
            share_pct=t.get("share_pct"),
        )
    
    # Tier bar chart
    st.markdown("<br>", unsafe_allow_html=True)
    chart = create_tier_bar_chart(tiers)
    st.plotly_chart(chart, use_container_width=True)

with col2:
    st.markdown("### Dominance Alerts")
    render_gold_accent()
    
    alerts = data["dominance_alerts"]
    
    if alerts:
        for alert in alerts:
            render_alert_card(
                level=alert["alert_level"],
                profession=alert["profession_name"],
                share_pct=alert["share_pct"],
                velocity=alert["velocity"],
                is_blocking=alert.get("is_blocking", False),
            )
    else:
        st.success("✓ No active dominance alerts")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Queue summary
    st.markdown("### Queue Summary")
    render_gold_accent()
    
    queue_counts = data["queue_counts"]
    total_queued = sum(queue_counts.values())
    
    st.metric("Total Queued Requests", total_queued)
    
    queue_cols = st.columns(4)
    for i, (tier, count) in enumerate(queue_counts.items()):
        with queue_cols[i]:
            st.metric(f"Tier {tier}", count)

# QVC Processing Capacity (only for QVC countries)
try:
    from app.utils.real_data_loader import get_qvc_capacity, is_qvc_country
    
    if is_qvc_country(selected_code):
        st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)
        st.markdown("### 🏢 QVC Processing Capacity")
        render_gold_accent()
        
        qvc_data = get_qvc_capacity(selected_code)
        if qvc_data:
            qvc_cols = st.columns(4)
            
            with qvc_cols[0]:
                render_metric_card(
                    label="Daily Capacity",
                    value=qvc_data['daily_capacity'],
                    icon="📅"
                )
            
            with qvc_cols[1]:
                render_metric_card(
                    label="Monthly Capacity",
                    value=f"{qvc_data['monthly_capacity']:,}",
                    delta="22 working days",
                    icon="📆"
                )
            
            with qvc_cols[2]:
                render_metric_card(
                    label="QVC Centers",
                    value=qvc_data['center_count'],
                    icon="🏛️"
                )
            
            with qvc_cols[3]:
                # Estimate days to process current headroom
                if qvc_data['daily_capacity'] > 0:
                    days_to_fill = data['headroom'] / qvc_data['daily_capacity']
                    render_metric_card(
                        label="Days to Fill Headroom",
                        value=f"{days_to_fill:.0f}",
                        delta="at full capacity",
                        icon="⏱️"
                    )
            
            # Show QVC center locations
            st.markdown("**QVC Center Locations:**")
            center_text = " • ".join([f"{c['city']} ({c['capacity']}/day)" for c in qvc_data['centers']])
            st.markdown(f"<div style='color: #5C5C7A; font-size: 0.9rem;'>{center_text}</div>", unsafe_allow_html=True)
    else:
        # Non-QVC country - show outflow-based capacity
        from app.utils.real_data_loader import is_non_qvc_country, get_outflow_capacity
        
        if is_non_qvc_country(selected_code):
            st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)
            st.markdown("### 📤 Monthly Allocation Capacity")
            render_gold_accent()
            
            outflow_data = get_outflow_capacity(selected_code)
            if outflow_data:
                st.markdown("""
                <div style="background: #FFF8E1; border-left: 4px solid #FFA000; padding: 0.75rem 1rem; margin-bottom: 1rem; border-radius: 4px;">
                    <strong>Outflow-Based Model:</strong> Monthly capacity = workers who left previous month (replacement slots)
                </div>
                """, unsafe_allow_html=True)
                
                outflow_cols = st.columns(4)
                
                with outflow_cols[0]:
                    render_metric_card(
                        label="Monthly Capacity",
                        value=outflow_data['monthly_capacity'],
                        delta="replacement slots",
                        icon="📅"
                    )
                
                with outflow_cols[1]:
                    render_metric_card(
                        label="Annual Outflow",
                        value=f"{outflow_data['annual_outflow']:,}",
                        delta="workers left 2025",
                        icon="📤"
                    )
                
                with outflow_cols[2]:
                    render_metric_card(
                        label="Growth Rate",
                        value=f"{outflow_data['growth_rate']:+.1f}%",
                        delta="YoY change",
                        icon="📉"
                    )
                
                with outflow_cols[3]:
                    # Days to fill headroom at current outflow rate
                    if outflow_data['monthly_capacity'] > 0:
                        months_to_fill = data['headroom'] / outflow_data['monthly_capacity']
                        render_metric_card(
                            label="Months to Fill Headroom",
                            value=f"{months_to_fill:.1f}",
                            delta="at current outflow",
                            icon="⏱️"
                        )
                
                st.markdown(f"<div style='color: #5C5C7A; font-size: 0.9rem;'>{outflow_data['description']}</div>", unsafe_allow_html=True)
        else:
            # Afghanistan or other - no special processing info
            st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)
            st.info(f"ℹ️ {NATIONALITIES.get(selected_code, selected_code)} follows standard visa processing procedures.")
        
except Exception as e:
    pass  # Capacity data not available

# Headroom gauge
st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)
st.markdown("### Capacity Overview")
render_gold_accent()

gauge_cols = st.columns([1, 2, 1])
with gauge_cols[1]:
    gauge = create_headroom_gauge(
        current=data["stock"],
        maximum=data["cap"],
        title=f"{data['nationality_code']} Utilization"
    )
    st.plotly_chart(gauge, use_container_width=True)

# Last updated
st.markdown(f"""
<div style="text-align: center; color: #5C5C7A; font-size: 0.85rem; margin-top: 2rem;">
    Last updated: {data.get('last_updated', 'N/A')}
</div>
""", unsafe_allow_html=True)
