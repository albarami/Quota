"""
Live Dashboard Page - v4 Implementation.

Real-time monitoring of nationality quotas using the v4 methodology.
All data is loaded directly from the quota_engine - no fallbacks.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import datetime

from app.components.styles import apply_custom_css, render_header, render_gold_accent
from app.components.charts import (
    create_headroom_gauge,
    create_tier_bar_chart,
    create_qvc_utilization_gauge,
    create_cap_constraint_chart,
)
from app.components.cards import (
    render_metric_card,
    render_tier_card,
    render_alert_card,
    render_utilization_bar,
    render_qvc_constraint_card,
    render_growth_direction_card,
    render_cap_formula_breakdown,
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
    "Real-time monitoring using v4 methodology"
)

# Restricted nationalities
NATIONALITIES = {
    "IND": "India",
    "BGD": "Bangladesh",
    "NPL": "Nepal",
    "PAK": "Pakistan",
    "PHL": "Philippines",
    "LKA": "Sri Lanka",
    "EGY": "Egypt",
    "YEM": "Yemen",
    "SYR": "Syria",
    "IRN": "Iran",
    "IRQ": "Iraq",
    "AFG": "Afghanistan",
}

# Nationality selector
st.markdown("### Select Nationality")
render_gold_accent()

selected_code = st.selectbox(
    "Nationality",
    options=list(NATIONALITIES.keys()),
    format_func=lambda x: f"{x} - {NATIONALITIES[x]}",
    label_visibility="collapsed",
)


def fetch_dashboard_data(nationality_code: str):
    """
    Fetch dashboard data from quota engine.
    No fallbacks - production data only.
    """
    from app.utils.real_data_loader import get_real_dashboard_data, check_real_data_available
    
    if not check_real_data_available():
        st.error("Real data files not found in real_data/ folder. Please ensure data is available.")
        return None
    
    return get_real_dashboard_data(nationality_code)


# Fetch data
data = fetch_dashboard_data(selected_code)

if data is None:
    st.stop()

# ============================================================
# KPI Row - v4 Metrics
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
kpi_cols = st.columns(4)

with kpi_cols[0]:
    render_metric_card(
        label="Recommended Cap",
        value=data["recommended_cap"],
        delta="v4 Formula" if data.get("is_qvc_constrained") else "Demand-Based",
        icon="🎯"
    )

with kpi_cols[1]:
    render_metric_card(
        label="Current Stock",
        value=data["stock"],
        delta=f"{data['utilization_pct']*100:.1f}% utilized",
        icon="👥"
    )

with kpi_cols[2]:
    render_metric_card(
        label="Headroom",
        value=data["headroom"],
        delta="available capacity",
        icon="📈"
    )

with kpi_cols[3]:
    growth = data.get("growth_rate", 0)
    direction = data.get("growth_direction", "NEGATIVE")
    render_metric_card(
        label="Growth",
        value=f"{growth:+.1f}%",
        delta=direction,
        delta_color="normal" if direction == "POSITIVE" else "inverse",
        icon="📊"
    )

st.markdown("<br>", unsafe_allow_html=True)

# Utilization bar
render_utilization_bar(
    current=data["stock"],
    maximum=data["recommended_cap"],
    label=f"{data['nationality_code']} Cap Utilization"
)

st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)

# ============================================================
# QVC Constraint Section (for QVC countries)
# ============================================================
if data.get("country_type") == "QVC" and data.get("qvc_annual_capacity"):
    st.markdown("### QVC Capacity Constraint")
    render_gold_accent()
    
    render_qvc_constraint_card(
        is_constrained=data.get("is_qvc_constrained", False),
        desired_cap=data.get("desired_cap", 0),
        max_achievable=data.get("max_achievable_cap", 0),
        net_qvc_capacity=data.get("net_qvc_capacity", 0),
    )
    
    st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)

# ============================================================
# Cap Calculation Breakdown (expandable)
# ============================================================
with st.expander("📐 Cap Calculation Details (v4 Formula)", expanded=False):
    calc_cols = st.columns([2, 1])
    
    with calc_cols[0]:
        render_cap_formula_breakdown(
            stock=data["stock"],
            demand_basis=data.get("demand_basis", "Outflow"),
            demand_value=data.get("demand_value", 0),
            buffer_pct=data.get("buffer_pct", 0.05),
            buffer_value=data.get("buffer_value", 0),
            desired_cap=data.get("desired_cap", 0),
            qvc_annual=data.get("qvc_annual_capacity"),
            net_qvc=data.get("net_qvc_capacity"),
            max_achievable=data.get("max_achievable_cap"),
            recommended_cap=data["recommended_cap"],
            is_constrained=data.get("is_qvc_constrained", False),
            country_type=data.get("country_type", "QVC"),
        )
    
    with calc_cols[1]:
        render_growth_direction_card(
            direction=data.get("growth_direction", "NEGATIVE"),
            joiners=data.get("avg_annual_joiners", 0),
            outflow=data.get("avg_annual_outflow", 0),
            demand_basis=data.get("demand_basis", "Outflow"),
        )

st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)

# ============================================================
# Two columns: Tier Status and Alerts
# ============================================================
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Tier Status")
    render_gold_accent()
    
    # Tier cards in 2x2 grid
    tier_row1 = st.columns(2)
    tier_row2 = st.columns(2)
    
    tiers = data.get("tier_statuses", [])
    
    if len(tiers) >= 4:
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
    if tiers:
        st.markdown("<br>", unsafe_allow_html=True)
        chart = create_tier_bar_chart(tiers)
        st.plotly_chart(chart, use_container_width=True)

with col2:
    st.markdown("### Dominance Alerts")
    render_gold_accent()
    
    alerts = data.get("dominance_alerts", [])
    
    if alerts:
        for alert in alerts[:5]:  # Show top 5
            render_alert_card(
                level=alert.get("alert_level", "WATCH"),
                profession=alert.get("profession_name", "Unknown"),
                share_pct=alert.get("share_pct", 0),
                velocity=alert.get("velocity", 0.02),
                is_blocking=alert.get("is_blocking", False),
            )
    else:
        st.success("✓ No active dominance alerts")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Queue summary
    st.markdown("### Queue Summary")
    render_gold_accent()
    
    queue_counts = data.get("queue_counts", {1: 0, 2: 0, 3: 0, 4: 0})
    total_queued = sum(queue_counts.values())
    
    st.metric("Total Queued Requests", total_queued)
    
    queue_cols = st.columns(4)
    for i, (tier, count) in enumerate(queue_counts.items()):
        with queue_cols[i]:
            st.metric(f"Tier {tier}", count)

# ============================================================
# QVC / Outflow Capacity Section
# ============================================================
st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)

from app.utils.real_data_loader import is_qvc_country, is_non_qvc_country, get_qvc_capacity, get_outflow_capacity

if is_qvc_country(selected_code):
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
                label="Annual Capacity",
                value=f"{qvc_data['annual_capacity']:,}",
                delta=f"{qvc_data['monthly_capacity']:,}/month",
                icon="📆"
            )
        
        with qvc_cols[2]:
            render_metric_card(
                label="QVC Centers",
                value=qvc_data['center_count'],
                icon="🏛️"
            )
        
        with qvc_cols[3]:
            # Show QVC utilization for replacement
            if data.get("avg_annual_outflow") and qvc_data['annual_capacity']:
                qvc_util = data["avg_annual_outflow"] / qvc_data['annual_capacity'] * 100
                render_metric_card(
                    label="Replacement Usage",
                    value=f"{qvc_util:.1f}%",
                    delta="of QVC capacity",
                    icon="🔄"
                )
        
        # QVC Utilization Gauge
        if data.get("avg_annual_outflow") and qvc_data['annual_capacity']:
            st.markdown("<br>", unsafe_allow_html=True)
            gauge = create_qvc_utilization_gauge(
                outflow=data["avg_annual_outflow"],
                qvc_annual=qvc_data['annual_capacity'],
            )
            st.plotly_chart(gauge, use_container_width=True)
        
        # Show QVC center locations
        st.markdown("**QVC Center Locations:**")
        center_text = " • ".join([f"{c['city']} ({c['capacity']}/day)" for c in qvc_data['centers']])
        st.markdown(f"<div style='color: #5C5C7A; font-size: 0.9rem;'>{center_text}</div>", unsafe_allow_html=True)

elif is_non_qvc_country(selected_code):
    st.markdown("### 📤 Monthly Allocation Capacity")
    render_gold_accent()
    
    outflow_data = get_outflow_capacity(selected_code)
    if outflow_data:
        st.markdown("""
        <div style="background: #FFF8E1; border-left: 4px solid #FFA000; padding: 0.75rem 1rem; margin-bottom: 1rem; border-radius: 4px;">
            <strong>Outflow-Based Model:</strong> Cap frozen at stock. Monthly capacity = workers who left (replacement slots)
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
                delta="avg workers leaving",
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
            render_metric_card(
                label="Stock",
                value=f"{outflow_data['current_stock']:,}",
                delta="= Cap (frozen)",
                icon="🔒"
            )
        
        st.markdown(f"<div style='color: #5C5C7A; font-size: 0.9rem;'>{outflow_data['description']}</div>", unsafe_allow_html=True)

else:
    # Afghanistan or other standard non-QVC
    st.markdown("### Standard Processing")
    render_gold_accent()
    st.info(f"ℹ️ {NATIONALITIES.get(selected_code, selected_code)} follows standard visa processing (non-QVC, non-frozen).")

# ============================================================
# Capacity Overview Gauge
# ============================================================
st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)
st.markdown("### Capacity Overview")
render_gold_accent()

gauge_cols = st.columns([1, 2, 1])
with gauge_cols[1]:
    gauge = create_headroom_gauge(
        current=data["stock"],
        maximum=data["recommended_cap"],
        title=f"{data['nationality_code']} Utilization"
    )
    st.plotly_chart(gauge, use_container_width=True)

# Last updated
st.markdown(f"""
<div style="text-align: center; color: #5C5C7A; font-size: 0.85rem; margin-top: 2rem;">
    Last updated: {data.get('last_updated', datetime.now().isoformat())} | 
    Data source: {data.get('data_source', 'quota_engine_v4')} |
    Formula: v{data.get('formula_version', '4.0')}
</div>
""", unsafe_allow_html=True)
