"""
Cap Management Page.

Set and manage nationality caps with AI recommendations.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import requests
from datetime import date

from app.components.styles import apply_custom_css, render_header, render_gold_accent, render_info_box
from app.components.charts import create_cap_recommendation_chart
from app.components.cards import render_metric_card


st.set_page_config(
    page_title="Cap Management | Qatar Quota System",
    page_icon="🎯",
    layout="wide",
)

apply_custom_css()

# Header
render_header(
    "Cap Management",
    "Set and manage annual nationality caps with AI-powered recommendations"
)

API_BASE = st.session_state.get("api_base_url", "http://localhost:8000")

# Nationality selector
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

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Select Nationality")
    render_gold_accent()
    
    selected_code = st.selectbox(
        "Nationality",
        options=list(NATIONALITIES.keys()),
        format_func=lambda x: f"{x} - {NATIONALITIES[x]}",
        label_visibility="collapsed",
        key="cap_nationality",
    )

with col2:
    st.markdown("### Year")
    render_gold_accent()
    
    selected_year = st.selectbox(
        "Year",
        options=[2026, 2025, 2024],
        label_visibility="collapsed",
    )


def fetch_cap_data(nationality_code: str, year: int):
    """Fetch current cap data."""
    try:
        response = requests.get(
            f"{API_BASE}/api/v1/caps/{nationality_code}?year={year}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Demo data
    return {
        "nationality_id": 1,
        "nationality_code": nationality_code,
        "year": year,
        "cap_limit": 15000,
        "previous_cap": 14000,
        "set_by": "Policy Committee",
        "set_date": "2025-12-15",
    }


def fetch_recommendation(nationality_code: str):
    """Fetch AI cap recommendation."""
    try:
        response = requests.get(
            f"{API_BASE}/api/v1/caps/{nationality_code}/recommendation",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Demo recommendation
    return {
        "nationality_id": 1,
        "nationality_code": nationality_code,
        "current_stock": 12450,
        "current_cap": 15000,
        "conservative_cap": 15750,
        "moderate_cap": 16500,
        "flexible_cap": 18000,
        "recommended_cap": 16500,
        "recommendation_level": "moderate",
        "rationale": (
            f"A moderate cap of 16,500 is recommended for {nationality_code}, "
            f"allowing 10% growth from current levels. This balances demand accommodation "
            f"with concentration risk management. Current stock is 12,450."
        ),
        "key_factors": [
            "Current stock: 12,450 workers",
            "Current cap: 15,000",
            "Utilization: 83%",
            "Active dominance alerts: 2",
        ],
        "risks": [
            "HIGH dominance alerts in Construction sector",
            "Near cap limit - may create backlogs",
        ],
    }


# Current cap section
st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)

cap_data = fetch_cap_data(selected_code, selected_year)

st.markdown("### Current Cap Configuration")
render_gold_accent()

cap_cols = st.columns(4)

with cap_cols[0]:
    render_metric_card(
        label="Current Cap",
        value=cap_data["cap_limit"],
        icon="🎯"
    )

with cap_cols[1]:
    render_metric_card(
        label="Previous Cap",
        value=cap_data.get("previous_cap") or "N/A",
        icon="📊"
    )

with cap_cols[2]:
    change = ""
    if cap_data.get("previous_cap"):
        diff = cap_data["cap_limit"] - cap_data["previous_cap"]
        pct = diff / cap_data["previous_cap"] * 100
        change = f"{diff:+,} ({pct:+.1f}%)"
    render_metric_card(
        label="Change",
        value=change or "N/A",
        icon="📈"
    )

with cap_cols[3]:
    render_metric_card(
        label="Set By",
        value=cap_data.get("set_by", "N/A"),
        icon="👤"
    )

# AI Recommendation section
st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)
st.markdown("### 🤖 AI Recommendation")
render_gold_accent()

with st.spinner("Generating AI recommendation..."):
    recommendation = fetch_recommendation(selected_code)

rec_cols = st.columns([2, 1])

with rec_cols[0]:
    # Options chart
    chart = create_cap_recommendation_chart(
        current=recommendation["current_cap"],
        conservative=recommendation["conservative_cap"],
        moderate=recommendation["moderate_cap"],
        flexible=recommendation["flexible_cap"],
        recommended=recommendation["recommended_cap"],
    )
    st.plotly_chart(chart, use_container_width=True)

with rec_cols[1]:
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #F8F5F0 0%, #FFFFFF 100%);
        border: 2px solid #D4AF37;
        border-radius: 12px;
        padding: 1.5rem;
    ">
        <h4 style="color: #7B1E3D; margin: 0 0 1rem 0;">
            ★ Recommended: {recommendation['recommendation_level'].title()}
        </h4>
        <div style="font-size: 2rem; font-weight: 700; color: #D4AF37;">
            {recommendation['recommended_cap']:,}
        </div>
        <p style="color: #5C5C7A; font-size: 0.9rem; margin-top: 1rem;">
            {recommendation['rationale']}
        </p>
    </div>
    """, unsafe_allow_html=True)

# Key factors and risks
factor_cols = st.columns(2)

with factor_cols[0]:
    st.markdown("#### Key Factors")
    for factor in recommendation["key_factors"]:
        st.markdown(f"- {factor}")

with factor_cols[1]:
    st.markdown("#### Risks")
    for risk in recommendation["risks"]:
        st.markdown(f"- ⚠️ {risk}")

# Set new cap form
st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)
st.markdown("### Set New Cap")
render_gold_accent()

render_info_box(
    "Setting a new cap requires Policy Committee authorization. "
    "This form is for demonstration purposes only."
)

form_cols = st.columns([2, 1, 1])

with form_cols[0]:
    new_cap = st.number_input(
        "New Cap Limit",
        min_value=1000,
        max_value=100000,
        value=recommendation["recommended_cap"],
        step=500,
        help="Enter the new annual cap limit for this nationality"
    )

with form_cols[1]:
    option = st.radio(
        "Quick Select",
        ["Conservative", "Moderate", "Flexible", "Custom"],
        index=1,
        horizontal=True,
    )
    
    if option == "Conservative":
        new_cap = recommendation["conservative_cap"]
    elif option == "Moderate":
        new_cap = recommendation["moderate_cap"]
    elif option == "Flexible":
        new_cap = recommendation["flexible_cap"]

with form_cols[2]:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Apply Cap", type="primary", use_container_width=True):
        # Would call API in production
        st.success(f"Cap updated to {new_cap:,} for {selected_code}")
        st.balloons()

# Display impact preview
if new_cap != cap_data["cap_limit"]:
    st.markdown("#### Impact Preview")
    
    impact_cols = st.columns(4)
    diff = new_cap - cap_data["cap_limit"]
    pct = diff / cap_data["cap_limit"] * 100
    
    with impact_cols[0]:
        st.metric("New Cap", f"{new_cap:,}")
    with impact_cols[1]:
        st.metric("Change", f"{diff:+,}")
    with impact_cols[2]:
        st.metric("Percentage", f"{pct:+.1f}%")
    with impact_cols[3]:
        st.metric("Est. New Headroom", f"{new_cap - 12450:,}")
