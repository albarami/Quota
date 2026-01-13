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

# Restricted nationalities (would come from API in production)
NATIONALITIES = {
    "EGY": "Egypt",
    "BGD": "Bangladesh",
    "IND": "India",
    "NPL": "Nepal",
    "PAK": "Pakistan",
    "LKA": "Sri Lanka",
    "PHL": "Philippines",
    "IDN": "Indonesia",
    "VNM": "Vietnam",
    "KEN": "Kenya",
    "ETH": "Ethiopia",
}

selected_code = st.selectbox(
    "Nationality",
    options=list(NATIONALITIES.keys()),
    format_func=lambda x: f"{x} - {NATIONALITIES[x]}",
    label_visibility="collapsed",
)


def fetch_dashboard_data(nationality_code: str):
    """Fetch dashboard data from API."""
    try:
        response = requests.get(
            f"{API_BASE}/api/v1/dashboard/{nationality_code}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.warning(f"Could not connect to API. Using demo data. ({e})")
    
    # Return demo data if API unavailable
    return {
        "nationality_id": 1,
        "nationality_code": nationality_code,
        "nationality_name": NATIONALITIES.get(nationality_code, nationality_code),
        "cap": 15000,
        "stock": 12450,
        "headroom": 1875,
        "utilization_pct": 0.83,
        "tier_statuses": [
            {"tier_level": 1, "tier_name": "Primary", "status": "OPEN", "capacity": 800, "share_pct": 0.33},
            {"tier_level": 2, "tier_name": "Secondary", "status": "RATIONED", "capacity": 320, "share_pct": 0.12},
            {"tier_level": 3, "tier_name": "Minor", "status": "LIMITED", "capacity": 45, "share_pct": 0.03},
            {"tier_level": 4, "tier_name": "Unusual", "status": "CLOSED", "capacity": 0, "share_pct": 0.01},
        ],
        "dominance_alerts": [
            {
                "profession_id": 1,
                "profession_name": "Construction Supervisor",
                "share_pct": 0.52,
                "velocity": 0.08,
                "alert_level": "CRITICAL",
                "is_blocking": True,
            },
            {
                "profession_id": 2,
                "profession_name": "Site Engineer",
                "share_pct": 0.42,
                "velocity": 0.04,
                "alert_level": "HIGH",
                "is_blocking": False,
            },
        ],
        "queue_counts": {1: 45, 2: 89, 3: 12, 4: 3},
        "projected_outflow": 187,
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
