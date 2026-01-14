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
            timeout=2
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Dynamic demo data per nationality
    return _generate_cap_demo_data(nationality_code, year)


def _generate_cap_demo_data(nationality_code: str, year: int) -> dict:
    """Generate realistic cap data that varies by nationality."""
    # Realistic data per nationality
    demo_caps = {
        "EGY": {"cap": 45000, "prev": 42000},
        "IND": {"cap": 85000, "prev": 80000},
        "PAK": {"cap": 35000, "prev": 33000},
        "NPL": {"cap": 55000, "prev": 52000},
        "BGD": {"cap": 62000, "prev": 58000},
        "PHL": {"cap": 28000, "prev": 26000},
        "IRN": {"cap": 8000, "prev": 7500},
        "IRQ": {"cap": 12000, "prev": 11000},
        "YEM": {"cap": 6000, "prev": 5500},
        "SYR": {"cap": 9500, "prev": 9000},
        "AFG": {"cap": 7500, "prev": 7000},
    }
    
    data = demo_caps.get(nationality_code, {"cap": 15000, "prev": 14000})
    
    # Adjust by year
    year_adj = (year - 2024) * 0.05  # 5% growth per year
    cap_limit = int(data["cap"] * (1 + year_adj))
    prev_cap = int(data["prev"] * (1 + year_adj))
    
    return {
        "nationality_id": list(NATIONALITIES.keys()).index(nationality_code) + 1 if nationality_code in NATIONALITIES else 1,
        "nationality_code": nationality_code,
        "year": year,
        "cap_limit": cap_limit,
        "previous_cap": prev_cap,
        "set_by": "Policy Committee",
        "set_date": f"{year-1}-12-15",
    }


def fetch_recommendation(nationality_code: str):
    """Fetch AI cap recommendation."""
    try:
        response = requests.get(
            f"{API_BASE}/api/v1/caps/{nationality_code}/recommendation",
            timeout=2
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Dynamic demo recommendation
    return _generate_recommendation_demo(nationality_code)


def _generate_recommendation_demo(nationality_code: str) -> dict:
    """Generate realistic AI recommendation that varies by nationality."""
    # Base data per nationality
    demo_profiles = {
        "EGY": {"stock": 38500, "cap": 45000, "alerts": 3, "level": "moderate"},
        "IND": {"stock": 78200, "cap": 85000, "alerts": 5, "level": "conservative"},
        "PAK": {"stock": 29800, "cap": 35000, "alerts": 2, "level": "moderate"},
        "NPL": {"stock": 48900, "cap": 55000, "alerts": 3, "level": "moderate"},
        "BGD": {"stock": 54300, "cap": 62000, "alerts": 4, "level": "conservative"},
        "PHL": {"stock": 21500, "cap": 28000, "alerts": 1, "level": "flexible"},
        "IRN": {"stock": 5200, "cap": 8000, "alerts": 1, "level": "flexible"},
        "IRQ": {"stock": 9800, "cap": 12000, "alerts": 2, "level": "moderate"},
        "YEM": {"stock": 4100, "cap": 6000, "alerts": 1, "level": "flexible"},
        "SYR": {"stock": 7200, "cap": 9500, "alerts": 1, "level": "moderate"},
        "AFG": {"stock": 5800, "cap": 7500, "alerts": 2, "level": "moderate"},
    }
    
    profile = demo_profiles.get(nationality_code, {"stock": 12450, "cap": 15000, "alerts": 2, "level": "moderate"})
    
    stock = profile["stock"]
    cap = profile["cap"]
    level = profile["level"]
    alerts = profile["alerts"]
    utilization = stock / cap if cap > 0 else 0
    
    # Calculate recommendations
    conservative = int(cap * 1.05)
    moderate = int(cap * 1.10)
    flexible = int(cap * 1.20)
    
    if level == "conservative":
        recommended = conservative
    elif level == "flexible":
        recommended = flexible
    else:
        recommended = moderate
    
    country_name = NATIONALITIES.get(nationality_code, nationality_code)
    
    # Dynamic rationale
    if level == "conservative":
        rationale = (
            f"A conservative cap of {conservative:,} is recommended for {country_name} "
            f"due to {alerts} active dominance alerts. This limits growth to 5% while "
            f"maintaining workforce diversification goals. Current stock is {stock:,}."
        )
    elif level == "flexible":
        rationale = (
            f"A flexible cap of {flexible:,} is recommended for {country_name}, "
            f"enabling 20% growth to meet strong demand. With only {alerts} alert(s) and "
            f"{utilization:.0%} utilization, there is room for expansion. Current stock is {stock:,}."
        )
    else:
        rationale = (
            f"A moderate cap of {moderate:,} is recommended for {country_name}, "
            f"allowing 10% growth from current levels. This balances demand accommodation "
            f"with concentration risk management. Current stock is {stock:,}."
        )
    
    return {
        "nationality_id": list(NATIONALITIES.keys()).index(nationality_code) + 1 if nationality_code in NATIONALITIES else 1,
        "nationality_code": nationality_code,
        "current_stock": stock,
        "current_cap": cap,
        "conservative_cap": conservative,
        "moderate_cap": moderate,
        "flexible_cap": flexible,
        "recommended_cap": recommended,
        "recommendation_level": level,
        "rationale": rationale,
        "key_factors": [
            f"Current stock: {stock:,} workers",
            f"Current cap: {cap:,}",
            f"Utilization: {utilization:.0%}",
            f"Active dominance alerts: {alerts}",
        ],
        "risks": [
            f"{'CRITICAL' if alerts > 3 else 'HIGH' if alerts > 1 else 'WATCH'} dominance alerts in key sectors",
            "Near cap limit - may create backlogs" if utilization > 0.85 else "Monitor demand trends closely",
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

# Initialize session state for cap value
cap_key = f"new_cap_{selected_code}"
if cap_key not in st.session_state:
    st.session_state[cap_key] = recommendation["recommended_cap"]

with form_cols[1]:
    option = st.radio(
        "Quick Select",
        ["Custom", "Conservative", "Moderate", "Flexible"],
        index=0,
        horizontal=True,
        key=f"cap_option_{selected_code}",
    )
    
    # Update value based on quick select
    if option == "Conservative":
        default_value = recommendation["conservative_cap"]
    elif option == "Moderate":
        default_value = recommendation["moderate_cap"]
    elif option == "Flexible":
        default_value = recommendation["flexible_cap"]
    else:  # Custom
        default_value = st.session_state.get(cap_key, recommendation["recommended_cap"])

with form_cols[0]:
    new_cap = st.number_input(
        "New Cap Limit",
        min_value=1000,
        max_value=500000,
        value=default_value,
        step=500,
        help="Enter the new annual cap limit for this nationality",
        key=f"cap_input_{selected_code}",
    )
    # Store user's custom value
    st.session_state[cap_key] = new_cap

with form_cols[2]:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Apply Cap", type="primary", use_container_width=True):
        # Would call API in production
        st.success(f"✅ Cap updated to {new_cap:,} for {selected_code} ({NATIONALITIES[selected_code]})")

# Display impact preview
if new_cap != cap_data["cap_limit"]:
    st.markdown("#### Impact Preview")
    
    impact_cols = st.columns(4)
    diff = new_cap - cap_data["cap_limit"]
    pct = diff / cap_data["cap_limit"] * 100
    current_stock = recommendation["current_stock"]
    
    with impact_cols[0]:
        st.metric("New Cap", f"{new_cap:,}")
    with impact_cols[1]:
        st.metric("Change", f"{diff:+,}")
    with impact_cols[2]:
        st.metric("Percentage", f"{pct:+.1f}%")
    with impact_cols[3]:
        st.metric("Est. New Headroom", f"{new_cap - current_stock:,}")
