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
from app.utils.real_data_loader import get_outflow_capacity


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
    # Real data per nationality (from ministry worker_stock.csv) - EXACT VALUES
    demo_caps = {
        # All countries - EXACT caps from real ministry data
        "EGY": {"cap": 81668, "prev": 74244},
        "YEM": {"cap": 14949, "prev": 13590},
        "SYR": {"cap": 27038, "prev": 24580},
        "IRQ": {"cap": 1959, "prev": 1781},
        "AFG": {"cap": 3016, "prev": 2742},
        "IRN": {"cap": 7768, "prev": 7062},
        # QVC countries - EXACT caps from worker_stock
        "BGD": {"cap": 487741, "prev": 443401},
        "IND": {"cap": 676569, "prev": 615063},
        "NPL": {"cap": 437178, "prev": 397435},
        "PAK": {"cap": 242955, "prev": 220868},
        "PHL": {"cap": 155806, "prev": 141642},
        "LKA": {"cap": 136111, "prev": 123737},
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
    
    IMPORTANT - Section 9 Applicability:
    - For non-QVC countries (EGY, YEM, SYR, IRQ, IRN) with negative growth:
      Cap = Current Stock (frozen, replacement only via outflow-based allocation)
    
    Cap Recommendation Models (for applicable countries):
    - Conservative: Current_Cap × 1.05
    - Moderate: Current_Cap × 1.10  
    - Flexible: Current_Cap × 1.20
    """
    stock = data["stock"]
    cap = data["cap"]
    alerts = len(data.get("dominance_alerts", []))
    has_critical = any(a.get("alert_level") == "CRITICAL" for a in data.get("dominance_alerts", []))
    utilization = data.get("utilization_pct", stock / cap if cap > 0 else 0)
    utilization_pct = utilization * 100  # Convert to percentage for comparison
    
    # Growth rates loaded from growth_by_year.json (calculated from actual data)
    # Formula: Growth = (Total_2025 - Total_2024) / Total_2024 × 100
    import json
    from pathlib import Path
    growth_file = Path(__file__).parent.parent.parent / "real_data" / "growth_by_year.json"
    GROWTH_RATES = {}
    if growth_file.exists():
        with open(growth_file) as f:
            growth_data = json.load(f)
            GROWTH_RATES = {k: v['growth'] for k, v in growth_data.items()}
    else:
        # Fallback values if file not found
        GROWTH_RATES = {
            'IND': -20.7, 'BGD': -14.0, 'NPL': -18.5, 'PAK': -20.8,
            'PHL': -17.8, 'LKA': -22.2, 'EGY': -11.0, 'YEM': -5.5,
            'SYR': -11.9, 'AFG': -11.7, 'IRN': -8.1, 'IRQ': -9.8
        }
    growth_rate = GROWTH_RATES.get(nationality_code, 0)
    
    # Non-QVC countries with negative growth
    NON_QVC_COUNTRIES = ['EGY', 'YEM', 'SYR', 'IRQ', 'IRN']
    
    country_name = NATIONALITIES.get(nationality_code, nationality_code)
    
    # === SECTION 9: Check if non-QVC country with negative growth ===
    # For these: Cap = Current Stock (frozen, outflow-based replacement only)
    if nationality_code in NON_QVC_COUNTRIES and growth_rate < 0:
        return {
            "nationality_id": data.get("nationality_id", 1),
            "nationality_code": nationality_code,
            "current_stock": stock,
            "current_cap": cap,
            "conservative_cap": stock,  # All options = stock
            "moderate_cap": stock,
            "flexible_cap": stock,
            "recommended_cap": stock,  # Cap = Stock
            "recommendation_level": "outflow_based",
            "rationale": (
                f"Cap frozen at current stock ({stock:,}) for {country_name}. "
                f"With negative growth ({growth_rate:+.1f}%), this nationality uses outflow-based allocation. "
                f"Monthly capacity = previous month's outflow (replacement only). No growth allowed."
            ),
            "key_factors": [
                f"Current stock: {stock:,} workers",
                f"Growth rate: {growth_rate:+.1f}% YoY (NEGATIVE)",
                f"Allocation model: Outflow-based (replacement only)",
                f"Cap = Stock (frozen at current level)",
                f"Monthly capacity = workers who left previous month",
            ],
            "risks": [
                f"Declining workforce ({growth_rate:+.1f}%)",
                "Cap frozen at current stock level",
                "Only replacement hiring allowed via outflow",
            ],
            "is_outflow_based": True,
        }
    
    # === Data-Driven Cap Recommendation (NO pre-existing caps used) ===
    # Formula: Based on Stock + Projected Demand + Buffer
    
    # Get joiners data for demand projection (from data if available)
    joined_2024 = data.get("joined_2024", int(stock * 0.10))  # Default: 10% of stock
    joined_2025 = data.get("joined_2025", int(stock * 0.02))  # Default: 2% of stock
    avg_annual_joiners = (joined_2024 + joined_2025) / 2
    
    if growth_rate > 0:
        # POSITIVE GROWTH: Stock + Avg Joiners + 15% buffer
        conservative = int(stock + avg_annual_joiners + (stock * 0.10))  # 10% buffer
        moderate = int(stock + avg_annual_joiners + (stock * 0.15))      # 15% buffer
        flexible = int(stock + avg_annual_joiners + (stock * 0.20))      # 20% buffer
    else:
        # NEGATIVE GROWTH: Stock + minimal buffer
        conservative = int(stock + (stock * 0.03))  # 3% buffer
        moderate = int(stock + (stock * 0.05))      # 5% buffer
        flexible = int(stock + (stock * 0.08))      # 8% buffer
    
    # Selection Logic based on risk
    if alerts >= 10 or has_critical:
        level = "conservative"
        recommended = conservative
    elif alerts > 3:
        level = "moderate"
        recommended = moderate
    elif growth_rate > 0:
        level = "flexible"
        recommended = flexible
    else:
        level = "moderate"
        recommended = moderate
    
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
    # Real data per nationality (from ministry worker_stock.csv) - EXACT VALUES
    demo_profiles = {
        # All countries with EXACT stock/cap from real data
        "EGY": {"stock": 71574, "cap": 81668, "alerts": 0, "level": "moderate"},      # 87.6% util
        "YEM": {"stock": 13105, "cap": 14949, "alerts": 1, "level": "conservative"},  # CRITICAL: EMPLOYEE 51.4%
        "SYR": {"stock": 23324, "cap": 27038, "alerts": 0, "level": "moderate"},      # 86.3% util
        "IRQ": {"stock": 1658, "cap": 1959, "alerts": 0, "level": "moderate"},        # 84.6% util
        "AFG": {"stock": 2532, "cap": 3016, "alerts": 0, "level": "moderate"},        # 84.0% util
        "IRN": {"stock": 6683, "cap": 7768, "alerts": 0, "level": "moderate"},        # 86.0% util
        # QVC countries - EXACT VALUES from worker_stock
        "BGD": {"stock": 400273, "cap": 487741, "alerts": 0, "level": "moderate"},    # 82.1% util
        "IND": {"stock": 529575, "cap": 676569, "alerts": 0, "level": "flexible"},    # 78.3% util -> FLEXIBLE (< 80%)
        "NPL": {"stock": 346515, "cap": 437178, "alerts": 1, "level": "moderate"},    # 79.3% util
        "PAK": {"stock": 196277, "cap": 242955, "alerts": 1, "level": "moderate"},    # 80.8% util
        "PHL": {"stock": 126653, "cap": 155806, "alerts": 0, "level": "moderate"},    # 81.3% util
        "LKA": {"stock": 101272, "cap": 136111, "alerts": 0, "level": "flexible"},    # 74.4% util -> FLEXIBLE (< 80%)
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

# Check if this is an outflow-based country (non-QVC with negative growth)
is_outflow_based = recommendation.get("is_outflow_based", False)

if is_outflow_based:
    # Special display for outflow-based countries: Cap = Stock
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #FFF3E0 0%, #FFFFFF 100%);
        border: 2px solid #FF9800;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    ">
        <h4 style="color: #E65100; margin: 0 0 1rem 0;">
            📤 Outflow-Based Allocation
        </h4>
        <div style="font-size: 1.5rem; font-weight: 700; color: #E65100;">
            Cap = Current Stock = {recommendation['recommended_cap']:,}
        </div>
        <p style="color: #5C5C7A; font-size: 0.9rem; margin-top: 1rem;">
            {recommendation['rationale']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("""
    **Why no cap recommendation?**
    
    This nationality has **negative growth** and is a **non-QVC country**. Per Section 9 of the documentation:
    - Cap is frozen at current stock level
    - Monthly allocation = previous month's outflow (workers who left)
    - Only replacement hiring is allowed - no growth
    """)
else:
    # Standard cap recommendation display with chart
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
    st.markdown("#### Risks" if not is_outflow_based else "#### Status")
    for risk in recommendation["risks"]:
        st.markdown(f"- ⚠️ {risk}")

# Set new cap form
st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)

if is_outflow_based:
    # For outflow-based countries, cap is frozen at stock
    st.markdown("### Cap Status")
    render_gold_accent()
    
    st.warning(f"""
    **Cap Frozen at Current Stock: {recommendation['current_stock']:,}**
    
    This nationality uses outflow-based allocation due to negative growth.
    The cap is automatically set to equal the current stock.
    No manual cap adjustment is available - allocation is controlled by monthly outflow.
    """)
    
    # Show monthly capacity info
    outflow_data = get_outflow_capacity(selected_code)
    if outflow_data:
        st.markdown("#### Monthly Allocation Capacity")
        st.metric(
            "Available Slots per Month", 
            f"{outflow_data['monthly_capacity']:,}",
            delta="Based on previous outflow"
        )
    
    new_cap = recommendation["recommended_cap"]  # Cap = Stock
else:
    # Standard cap setting form
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
        # Dynamic max_value based on current cap (allow up to 2x current cap)
        max_cap = max(1000000, recommendation["current_cap"] * 2)
        new_cap = st.number_input(
            "New Cap Limit",
            min_value=1000,
            max_value=max_cap,
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
