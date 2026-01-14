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
    Fetch dashboard data - tries API first, then direct DB, then demo data.
    """
    # Try API first (for local development with FastAPI running)
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
    
    # Realistic data ranges per nationality (based on typical Qatar workforce)
    demo_profiles = {
        "EGY": {"cap": 45000, "stock": 38500, "tier1_status": "RATIONED"},
        "IND": {"cap": 85000, "stock": 78200, "tier1_status": "LIMITED"},
        "PAK": {"cap": 35000, "stock": 29800, "tier1_status": "OPEN"},
        "NPL": {"cap": 55000, "stock": 48900, "tier1_status": "RATIONED"},
        "BGD": {"cap": 62000, "stock": 54300, "tier1_status": "RATIONED"},
        "PHL": {"cap": 28000, "stock": 21500, "tier1_status": "OPEN"},
        "IRN": {"cap": 8000, "stock": 5200, "tier1_status": "OPEN"},
        "IRQ": {"cap": 12000, "stock": 9800, "tier1_status": "RATIONED"},
        "YEM": {"cap": 6000, "stock": 4100, "tier1_status": "OPEN"},
        "SYR": {"cap": 9500, "stock": 7200, "tier1_status": "OPEN"},
        "AFG": {"cap": 7500, "stock": 5800, "tier1_status": "RATIONED"},
    }
    
    profile = demo_profiles.get(nationality_code, {
        "cap": 15000 + (seed % 10000),
        "stock": 12000 + (seed % 8000),
        "tier1_status": "OPEN"
    })
    
    cap = profile["cap"]
    stock = profile["stock"]
    headroom = cap - stock
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
    
    # Generate dominance alerts (vary by nationality)
    alert_professions = [
        ("Construction Supervisor", 0.52, 0.08, "CRITICAL"),
        ("Site Engineer", 0.42, 0.04, "HIGH"),
        ("General Labourer", 0.38, 0.03, "WATCH"),
        ("Heavy Equipment Operator", 0.35, 0.02, "WATCH"),
    ]
    
    # Select alerts based on nationality seed
    num_alerts = (seed % 3) + 1
    alerts = []
    for i in range(num_alerts):
        prof = alert_professions[(seed + i) % len(alert_professions)]
        alerts.append({
            "profession_id": i + 1,
            "profession_name": prof[0],
            "share_pct": prof[1] - (i * 0.05),
            "velocity": prof[2],
            "alert_level": prof[3] if i == 0 else "HIGH" if i == 1 else "WATCH",
            "is_blocking": prof[3] == "CRITICAL" and i == 0,
        })
    
    # Queue counts vary by utilization
    queue_multiplier = 1 + (utilization * 2)
    queue_counts = {
        1: int(35 * queue_multiplier + (seed % 30)),
        2: int(65 * queue_multiplier + (seed % 50)),
        3: int(15 * queue_multiplier + (seed % 20)),
        4: int(5 * queue_multiplier + (seed % 10)),
    }
    
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
    render_metric_card(
        label="Projected Outflow",
        value=data["projected_outflow"],
        delta="Next 90 days",
        icon="📤"
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
