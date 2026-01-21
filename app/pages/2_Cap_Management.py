"""
Cap Management Page - v4 Implementation.

Manage and analyze nationality caps using the v4 methodology.
Shows detailed formula breakdown and QVC constraint analysis.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

from app.components.styles import apply_custom_css, render_header, render_gold_accent, COLORS
from app.components.charts import (
    create_cap_constraint_chart,
    create_qvc_utilization_gauge,
    create_v4_cap_breakdown_chart,
)
from app.components.cards import (
    render_metric_card,
    render_qvc_constraint_card,
    render_growth_direction_card,
    render_cap_formula_breakdown,
    render_utilization_bar,
)


st.set_page_config(
    page_title="Cap Management | Qatar Quota System",
    page_icon="📊",
    layout="wide",
)

apply_custom_css()

# Header
render_header(
    "Cap Management",
    "v4 Methodology - Demand-Driven Caps with QVC Constraints"
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
    """Fetch data using quota engine."""
    from app.utils.real_data_loader import get_real_dashboard_data, check_real_data_available
    
    if not check_real_data_available():
        st.error("Real data files not found in real_data/ folder.")
        return None
    
    return get_real_dashboard_data(nationality_code)


# Fetch data
data = fetch_dashboard_data(selected_code)

if data is None:
    st.stop()

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# Current Status Overview
# ============================================================
st.markdown("### Current Status")
render_gold_accent()

status_cols = st.columns(4)

with status_cols[0]:
    render_metric_card(
        label="Current Cap",
        value=data["recommended_cap"],  # Current = Recommended in v4
        delta="v4 recommended",
        icon="📋"
    )

with status_cols[1]:
    render_metric_card(
        label="Current Stock",
        value=data["stock"],
        icon="👥"
    )

with status_cols[2]:
    render_metric_card(
        label="Utilization",
        value=f"{data['utilization_pct']*100:.1f}%",
        delta_color="inverse" if data['utilization_pct'] > 0.9 else "normal",
        icon="📊"
    )

with status_cols[3]:
    render_metric_card(
        label="Headroom",
        value=data["headroom"],
        icon="📈"
    )

st.markdown("<br>", unsafe_allow_html=True)
render_utilization_bar(
    current=data["stock"],
    maximum=data["recommended_cap"],
    label="Current Cap Utilization"
)

st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)

# ============================================================
# v4 Cap Recommendation
# ============================================================
st.markdown("### 📐 v4 Cap Recommendation")
render_gold_accent()

st.markdown("""
<div style="background: #F8F5F0; border: 2px solid #C9A227; border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem;">
    <div style="font-weight: 700; color: #1A3A5C; margin-bottom: 0.5rem;">v4 Formula</div>
    <code style="font-size: 1rem;">Recommended_Cap = min(Stock + Demand + Buffer, Stock + Net_QVC)</code>
    <div style="font-size: 0.85rem; color: #5C5C7A; margin-top: 0.5rem;">
        where Demand = Joiners (positive growth) or Outflow (negative growth)
    </div>
</div>
""", unsafe_allow_html=True)

rec_cols = st.columns([3, 2])

with rec_cols[0]:
    # Step-by-step calculation
    st.markdown("#### Step-by-Step Calculation")
    
    # Step 1: Growth Direction
    st.markdown("**Step 1: Determine Growth Direction**")
    
    joiners = data.get("avg_annual_joiners", 0)
    outflow = data.get("avg_annual_outflow", 0)
    direction = data.get("growth_direction", "NEGATIVE")
    
    growth_cols = st.columns(3)
    with growth_cols[0]:
        st.metric("Avg Joiners/year", f"{joiners:,}")
    with growth_cols[1]:
        st.metric("Avg Outflow/year", f"{outflow:,}")
    with growth_cols[2]:
        color = "🟢" if direction == "POSITIVE" else "🔴"
        st.metric("Direction", f"{color} {direction}")
    
    st.markdown(f"""
    <div style="color: #5C5C7A; font-size: 0.9rem; margin: 0.5rem 0 1rem 0;">
        Growth is <strong>{direction}</strong> because 
        {"Joiners > Outflow" if direction == "POSITIVE" else "Outflow > Joiners"} 
        ({joiners:,} vs {outflow:,})
    </div>
    """, unsafe_allow_html=True)
    
    # Step 2: Demand Basis
    st.markdown("**Step 2: Select Demand Basis**")
    
    demand_basis = data.get("demand_basis", "Outflow")
    demand_value = data.get("demand_value", outflow)
    
    st.markdown(f"""
    <div style="background: {'#E8F5E9' if demand_basis == 'Joiners' else '#FFF8E1'}; 
                padding: 0.75rem; border-radius: 4px; margin-bottom: 1rem;">
        Using <strong>{demand_basis}</strong>: {demand_value:,} workers/year
        <div style="font-size: 0.85rem; color: #5C5C7A;">
            {"Positive growth uses Joiners as demand" if demand_basis == "Joiners" else "Negative/neutral growth uses Outflow as replacement capacity"}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Step 3: Calculate Desired Cap
    st.markdown("**Step 3: Calculate Desired Cap**")
    
    stock = data["stock"]
    buffer_pct = data.get("buffer_pct", 0.05)
    buffer_value = data.get("buffer_value", int(stock * buffer_pct))
    desired_cap = data.get("desired_cap", stock + demand_value + buffer_value)
    
    st.markdown(f"""
    <div style="font-family: 'Courier New', monospace; background: #f5f5f5; padding: 1rem; border-radius: 4px;">
        Stock:         {stock:>12,}<br>
        + {demand_basis}:{' ' * (10 - len(demand_basis))}{demand_value:>12,}<br>
        + Buffer ({buffer_pct*100:.0f}%):{' ' * (4 if buffer_pct < 0.1 else 3)}{buffer_value:>12,}<br>
        ─────────────────────────<br>
        = Desired Cap:  {desired_cap:>12,}
    </div>
    """, unsafe_allow_html=True)

with rec_cols[1]:
    render_growth_direction_card(
        direction=direction,
        joiners=joiners,
        outflow=outflow,
        demand_basis=demand_basis,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# QVC Constraint (for QVC countries)
# ============================================================
country_type = data.get("country_type", "")

if country_type == "QVC":
    st.markdown("**Step 4: Apply QVC Constraint**")
    
    qvc_annual = data.get("qvc_annual_capacity", 0)
    net_qvc = data.get("net_qvc_capacity", 0)
    max_achievable = data.get("max_achievable_cap", 0)
    is_constrained = data.get("is_qvc_constrained", False)
    
    qvc_cols = st.columns(2)
    
    with qvc_cols[0]:
        st.markdown(f"""
        <div style="font-family: 'Courier New', monospace; background: #E3F2FD; padding: 1rem; border-radius: 4px;">
            QVC Annual:    {qvc_annual:>12,}<br>
            - Outflow:     {outflow:>12,}<br>
            ─────────────────────────<br>
            = Net QVC:     {net_qvc:>12,}<br>
            <br>
            Max Achievable = Stock + Net QVC<br>
                           = {stock:,} + {net_qvc:,}<br>
                           = {max_achievable:,}
        </div>
        """, unsafe_allow_html=True)
    
    with qvc_cols[1]:
        render_qvc_constraint_card(
            is_constrained=is_constrained,
            desired_cap=desired_cap,
            max_achievable=max_achievable,
            net_qvc_capacity=net_qvc,
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Final Step
    st.markdown("**Step 5: Final Recommendation**")
    
    recommended = data["recommended_cap"]
    
    if is_constrained:
        st.markdown(f"""
        <div style="background: #FFEBEE; border-left: 4px solid #C62828; padding: 1rem; border-radius: 4px;">
            <div style="font-size: 1.1rem;">
                <strong>min(</strong>{desired_cap:,}, {max_achievable:,}<strong>)</strong> = 
                <span style="color: #C62828; font-weight: 700; font-size: 1.25rem;">{recommended:,}</span>
            </div>
            <div style="color: #C62828; margin-top: 0.5rem;">
                ⚠️ QVC CONSTRAINED: Desired cap exceeds QVC capacity by {desired_cap - max_achievable:,}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: #E8F5E9; border-left: 4px solid #2E7D32; padding: 1rem; border-radius: 4px;">
            <div style="font-size: 1.1rem;">
                <strong>min(</strong>{desired_cap:,}, {max_achievable:,}<strong>)</strong> = 
                <span style="color: #2E7D32; font-weight: 700; font-size: 1.25rem;">{recommended:,}</span>
            </div>
            <div style="color: #2E7D32; margin-top: 0.5rem;">
                ✓ Within QVC capacity
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Cap constraint chart
    st.markdown("<br>", unsafe_allow_html=True)
    chart = create_cap_constraint_chart(
        stock=stock,
        desired_cap=desired_cap,
        max_achievable=max_achievable,
        recommended_cap=recommended,
    )
    st.plotly_chart(chart, use_container_width=True)

elif country_type == "OUTFLOW_BASED":
    # Non-QVC outflow-based (frozen)
    st.markdown("**Step 4: Outflow-Based Model (Frozen Cap)**")
    
    st.markdown("""
    <div style="background: #FFF8E1; border-left: 4px solid #FFA000; padding: 1rem; border-radius: 4px;">
        <div style="font-weight: 700; color: #E65100;">⚠️ CAP FROZEN</div>
        <div style="margin-top: 0.5rem;">
            For non-QVC countries with negative growth, the cap is frozen at current stock.<br>
            Monthly allocation is based on outflow (replacement model).
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    monthly = data.get("monthly_allocation", outflow // 12)
    
    st.markdown(f"""
    <div style="font-family: 'Courier New', monospace; background: #f5f5f5; padding: 1rem; border-radius: 4px; margin-top: 1rem;">
        Recommended Cap:    {stock:>12,} (frozen at stock)<br>
        Monthly Allocation: {monthly:>12,} (based on outflow)<br>
        Headroom:           {0:>12,}
    </div>
    """, unsafe_allow_html=True)

else:
    # Standard non-QVC (Afghanistan)
    st.markdown("**Step 4: Standard Non-QVC (No QVC Constraint)**")
    
    recommended = data["recommended_cap"]
    
    st.markdown(f"""
    <div style="background: #E8F5E9; border-left: 4px solid #2E7D32; padding: 1rem; border-radius: 4px;">
        <div style="font-size: 1.1rem;">
            No QVC constraint applicable. Using demand-based formula directly.
        </div>
        <div style="font-weight: 700; font-size: 1.25rem; color: #2E7D32; margin-top: 0.5rem;">
            Recommended Cap: {recommended:,}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)

# ============================================================
# Summary Table
# ============================================================
st.markdown("### Summary")
render_gold_accent()

summary_data = {
    "Metric": [
        "Current Stock",
        "Avg Annual Joiners",
        "Avg Annual Outflow",
        "Growth Direction",
        "Demand Basis",
        "Buffer %",
        "Desired Cap",
        "QVC Annual Capacity" if country_type == "QVC" else "N/A",
        "Net QVC Capacity" if country_type == "QVC" else "N/A",
        "Max Achievable Cap" if country_type == "QVC" else "N/A",
        "QVC Constrained" if country_type == "QVC" else "N/A",
        "Recommended Cap",
        "Headroom",
        "Utilization %",
    ],
    "Value": [
        f"{data['stock']:,}",
        f"{joiners:,}",
        f"{outflow:,}",
        direction,
        demand_basis,
        f"{buffer_pct*100:.0f}%",
        f"{desired_cap:,}",
        f"{data.get('qvc_annual_capacity', 0):,}" if country_type == "QVC" else "N/A",
        f"{data.get('net_qvc_capacity', 0):,}" if country_type == "QVC" else "N/A",
        f"{data.get('max_achievable_cap', 0):,}" if country_type == "QVC" else "N/A",
        "YES" if data.get("is_qvc_constrained") else "No" if country_type == "QVC" else "N/A",
        f"{data['recommended_cap']:,}",
        f"{data['headroom']:,}",
        f"{data['utilization_pct']*100:.1f}%",
    ],
}

import pandas as pd
df = pd.DataFrame(summary_data)
df = df[df["Value"] != "N/A"]  # Remove N/A rows

st.dataframe(df, hide_index=True, use_container_width=True)

# ============================================================
# Formula Reference
# ============================================================
with st.expander("📚 Formula Reference (v4 Methodology)", expanded=False):
    st.markdown("""
    ### Country Classifications
    
    | Type | Countries | Treatment |
    |------|-----------|-----------|
    | **QVC** | BGD, IND, NPL, PAK, PHL, LKA | Subject to QVC capacity constraint |
    | **Outflow-Based** | EGY, YEM, SYR, IRN, IRQ | Cap frozen at stock, outflow-based allocation |
    | **Standard Non-QVC** | AFG | Standard formula without QVC constraint |
    
    ### Core Formula
    
    ```
    Recommended_Cap = min(Desired_Cap, Max_Achievable_Cap)
    
    where:
        Desired_Cap = Stock + Demand + Buffer
        Max_Achievable_Cap = Stock + Net_QVC_Capacity
        Net_QVC_Capacity = QVC_Annual - Avg_Outflow
    
    Demand Basis:
        - POSITIVE growth: Demand = Avg_Joiners
        - NEGATIVE growth: Demand = Avg_Outflow
    
    Buffer:
        - QVC + Positive: 10%
        - QVC + Negative: 5%
        - Standard Non-QVC: 5%
        - Outflow-Based: 0% (frozen)
    ```
    
    ### QVC Annual Capacity
    
    | Country | Daily | Monthly (×22) | Annual (×264) |
    |---------|-------|---------------|---------------|
    | India | 805 | 17,710 | 212,520 |
    | Bangladesh | 515 | 11,330 | 135,960 |
    | Pakistan | 370 | 8,140 | 97,680 |
    | Nepal | 325 | 7,150 | 85,800 |
    | Philippines | 280 | 6,160 | 73,920 |
    | Sri Lanka | 150 | 3,300 | 39,600 |
    """)

# Footer
st.markdown(f"""
<div style="text-align: center; color: #5C5C7A; font-size: 0.85rem; margin-top: 2rem;">
    Data source: {data.get('data_source', 'quota_engine_v4')} |
    Formula: v{data.get('formula_version', '4.0')} |
    Reference: Quota_Allocation_Methodology_v4.md
</div>
""", unsafe_allow_html=True)
