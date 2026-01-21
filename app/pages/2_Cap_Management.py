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
    "LKA": "Sri Lanka",
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
    """Fetch current cap data - tries real data first."""
    # Try real data from CSV files first
    try:
        from app.utils.real_data_loader import get_real_dashboard_data, check_real_data_available
        if check_real_data_available():
            data = get_real_dashboard_data(nationality_code)
            if data and data.get("cap", 0) > 0:
                return {
                    "nationality_id": data.get("nationality_id", 1),
                    "nationality_code": nationality_code,
                    "year": year,
                    "cap_limit": data["cap"],
                    "previous_cap": data.get("previous_cap", int(data["cap"] * 0.9)),
                    "set_by": "Ministry Policy",
                    "set_date": f"{year-1}-12-15",
                }
    except Exception as e:
        print(f"Real data load error: {e}")
    
    # Try API
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
    # Real data per nationality (from ministry data)
    demo_caps = {
        # Additional countries (Worker Stock) - caps from real data
        "EGY": {"cap": 81668, "prev": 74244},
        "YEM": {"cap": 14949, "prev": 13590},
        "SYR": {"cap": 27038, "prev": 24580},
        "IRQ": {"cap": 1959, "prev": 1781},
        "AFG": {"cap": 3016, "prev": 2742},
        "IRN": {"cap": 7062, "prev": 7062},  # Restricted
        # QVC countries (VP allocations)
        "BGD": {"cap": 69928, "prev": 63571},
        "IND": {"cap": 135369, "prev": 123063},
        "NPL": {"cap": 122988, "prev": 111807},
        "PAK": {"cap": 97870, "prev": 88973},
        "PHL": {"cap": 41540, "prev": 37764},
        "LKA": {"cap": 45541, "prev": 41401},
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
    """Fetch AI cap recommendation - uses real data when available."""
    # Try real data first for accurate stock/cap values
    try:
        from app.utils.real_data_loader import get_real_dashboard_data, check_real_data_available
        if check_real_data_available():
            data = get_real_dashboard_data(nationality_code)
            if data and data.get("stock", 0) > 0:
                return _build_recommendation_from_real_data(nationality_code, data)
    except Exception as e:
        print(f"Real data recommendation error: {e}")
    
    # Try API
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


def _build_recommendation_from_real_data(nationality_code: str, data: dict) -> dict:
    """
    Build AI recommendation using EXACT formulas from System_Documentation.md Section 9.
    
    Cap Recommendation Models (Section 9):
    - Conservative: Current_Cap × 1.05
    - Moderate: Current_Cap × 1.10  
    - Flexible: Current_Cap × 1.20
    
    Selection Logic (Section 9):
    IF dominance_alerts > 3 OR has_critical_alert:
        recommendation = CONSERVATIVE
    ELIF utilization > 90% OR dominance_alerts > 1:
        recommendation = MODERATE
    ELIF utilization < 80% AND dominance_alerts == 0:
        recommendation = FLEXIBLE
    ELSE:
        recommendation = MODERATE
    
    Growth Adjustment (Section 9):
    IF growth_rate > 5%:
        recommended_cap = recommended_cap × 1.05
    IF growth_rate < -5%:
        recommended_cap = recommended_cap × 0.95
    """
    stock = data["stock"]
    cap = data["cap"]
    alerts = len(data.get("dominance_alerts", []))
    has_critical = any(a.get("alert_level") == "CRITICAL" for a in data.get("dominance_alerts", []))
    utilization = data.get("utilization_pct", stock / cap if cap > 0 else 0)
    utilization_pct = utilization * 100  # Convert to percentage for comparison
    
    # Growth rates from ministry data (Section 10.G formula)
    # growth_rate = (net_change / current_stock) × 100
    GROWTH_RATES = {
        'EGY': -4.55,   # Egypt: -4.55%
        'YEM': -1.62,   # Yemen: -1.62%
        'SYR': -5.65,   # Syria: -5.65% (triggers reduction)
        'IRQ': -2.90,   # Iraq: -2.90%
        'AFG': +1.03,   # Afghanistan: +1.03%
        'IRN': 0.0,     # Iran: restricted
        'BGD': -2.0,    # Bangladesh: estimate
        'PAK': -1.0,    # Pakistan: estimate
        'IND': -1.5,    # India: estimate
        'NPL': -2.0,    # Nepal: estimate
        'PHL': -1.0,    # Philippines: estimate
        'LKA': -1.5,    # Sri Lanka: estimate
    }
    growth_rate = GROWTH_RATES.get(nationality_code, 0)
    
    # === STEP 1: Calculate base recommendations (Section 9 formulas) ===
    conservative = int(cap * 1.05)
    moderate = int(cap * 1.10)
    flexible = int(cap * 1.20)
    
    # === STEP 2: Selection Logic (EXACT from Section 9) ===
    if alerts > 3 or has_critical:
        level = "conservative"
        recommended = conservative
    elif utilization_pct > 90 or alerts > 1:
        level = "moderate"
        recommended = moderate
    elif utilization_pct < 80 and alerts == 0:
        level = "flexible"
        recommended = flexible
    else:
        level = "moderate"
        recommended = moderate
    
    # === STEP 3: Growth Adjustment (Section 9) ===
    if growth_rate > 5:
        recommended = int(recommended * 1.05)
    elif growth_rate < -5:
        recommended = int(recommended * 0.95)
    
    country_name = NATIONALITIES.get(nationality_code, nationality_code)
    
    # Build rationale explaining the decision
    if alerts > 0:
        alert_text = f"{alerts} active dominance alert(s)"
        alert_names = [a.get("profession_name", "Unknown") for a in data.get("dominance_alerts", [])[:2]]
        if alert_names:
            alert_text += f" ({', '.join(alert_names)})"
    else:
        alert_text = "no dominance alerts"
    
    growth_text = f"{growth_rate:+.1f}%" if growth_rate != 0 else "stable"
    
    # Explain why this level was selected
    if level == "conservative":
        if has_critical:
            reason = f"CRITICAL dominance alert detected"
        elif alerts > 3:
            reason = f"{alerts} dominance alerts exceed threshold"
        else:
            reason = "high risk factors present"
        rationale = (
            f"A conservative cap of {recommended:,} is recommended for {country_name}. "
            f"Reason: {reason}. Current utilization: {utilization_pct:.1f}%, growth: {growth_text}. "
            f"Current stock: {stock:,}."
        )
    elif level == "flexible":
        rationale = (
            f"A flexible cap of {recommended:,} is recommended for {country_name}. "
            f"With {utilization_pct:.1f}% utilization (<80%) and {alert_text}, "
            f"there is room for expansion. Growth: {growth_text}. Current stock: {stock:,}."
        )
    else:  # moderate
        if utilization_pct > 90:
            reason = f"high utilization ({utilization_pct:.1f}%)"
        elif alerts > 1:
            reason = f"{alerts} dominance alerts"
        else:
            reason = "balanced approach (utilization 80-90%)"
        rationale = (
            f"A moderate cap of {recommended:,} is recommended for {country_name}. "
            f"Reason: {reason}. Growth: {growth_text}, {alert_text}. Current stock: {stock:,}."
        )
    
    # Build risks list
    risks = []
    if alerts > 0:
        alert = data['dominance_alerts'][0]
        risks.append(f"{alert['alert_level']} alert: {alert['profession_name']} at {alert['share_pct']:.1%}")
    else:
        risks.append("No active dominance alerts")
    
    if growth_rate < -5:
        risks.append(f"Declining workforce ({growth_rate:+.1f}%) - cap reduced by 5%")
    elif growth_rate < 0:
        risks.append(f"Declining workforce ({growth_rate:+.1f}%) - monitor trends")
    elif growth_rate > 5:
        risks.append(f"Rapid growth ({growth_rate:+.1f}%) - cap increased by 5%")
    
    if utilization > 0.90:
        risks.append("Very high utilization (>90%) - backlogs likely")
    elif utilization > 0.85:
        risks.append("High utilization - monitor for backlogs")
    elif utilization < 0.50:
        risks.append("Low utilization (<50%) - cap may be over-allocated")
    
    return {
        "nationality_id": data.get("nationality_id", 1),
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
            f"Utilization: {utilization_pct:.1f}%",
            f"Growth rate: {growth_rate:+.1f}% YoY",
            f"Active dominance alerts: {alerts}",
        ],
        "risks": risks,
    }


def _generate_recommendation_demo(nationality_code: str) -> dict:
    """Generate realistic AI recommendation that varies by nationality."""
    # Real data per nationality (from ministry data)
    demo_profiles = {
        # Additional countries (Worker Stock data)
        "EGY": {"stock": 71574, "cap": 81668, "alerts": 0, "level": "moderate"},      # 87.6% util
        "YEM": {"stock": 13105, "cap": 14949, "alerts": 1, "level": "conservative"},  # CRITICAL: EMPLOYEE 51.4%
        "SYR": {"stock": 23324, "cap": 27038, "alerts": 0, "level": "moderate"},      # 86.3% util
        "IRQ": {"stock": 1658, "cap": 1959, "alerts": 0, "level": "moderate"},        # 84.6% util
        "AFG": {"stock": 2532, "cap": 3016, "alerts": 1, "level": "moderate"},        # DRIVER 21.6%
        "IRN": {"stock": 6683, "cap": 7062, "alerts": 0, "level": "conservative"},    # Restricted
        # QVC countries (VP data)
        "BGD": {"stock": 58544, "cap": 69928, "alerts": 0, "level": "flexible"},      # 83.7% util
        "IND": {"stock": 43847, "cap": 135369, "alerts": 0, "level": "conservative"}, # 32.4% util
        "NPL": {"stock": 40955, "cap": 122988, "alerts": 1, "level": "conservative"}, # LABOURER 18.7%
        "PAK": {"stock": 61154, "cap": 97870, "alerts": 1, "level": "conservative"},  # WATCH: DRIVER 30.7%
        "PHL": {"stock": 7078, "cap": 41540, "alerts": 0, "level": "conservative"},   # 17.0% util
        "LKA": {"stock": 12609, "cap": 45541, "alerts": 0, "level": "conservative"},  # 27.7% util
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
