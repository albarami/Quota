"""
Request Portal Page.

Submit quota requests with real-time eligibility checking.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import requests
from datetime import datetime

from app.components.styles import (
    apply_custom_css, 
    render_header, 
    render_gold_accent,
    render_alert_box,
    render_info_box,
)
from app.components.cards import render_status_card, render_metric_card


st.set_page_config(
    page_title="Request Portal | Qatar Quota System",
    page_icon="📝",
    layout="wide",
)

apply_custom_css()

# Header
render_header(
    "Request Portal",
    "Submit quota requests with real-time eligibility checking"
)

API_BASE = st.session_state.get("api_base_url", "http://localhost:8000")

# Demo data
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

PROFESSIONS = {
    1: "Construction Supervisor",
    2: "Site Engineer",
    3: "General Labourer",
    4: "Electrician",
    5: "Plumber",
    6: "Welder",
    7: "Heavy Equipment Operator",
    8: "Security Guard",
    9: "Driver",
    10: "Cleaner",
}

ESTABLISHMENTS = {
    1: "Al Rayyan Construction LLC",
    2: "Qatar Building Company",
    3: "Gulf Services WLL",
    4: "Doha Maintenance Co.",
    5: "National Contracting Ltd.",
}


def check_eligibility(nationality_id: int, profession_id: int, establishment_id: int, count: int):
    """Check eligibility for request."""
    try:
        response = requests.post(
            f"{API_BASE}/api/v1/requests/check-eligibility",
            json={
                "nationality_id": nationality_id,
                "profession_id": profession_id,
                "establishment_id": establishment_id,
                "requested_count": count,
            },
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Demo response
    return {
        "is_eligible": True,
        "tier_level": 1,
        "tier_name": "Primary",
        "tier_status": "OPEN",
        "dominance_alert": None,
        "estimated_outcome": "APPROVED",
        "priority_score": 80,
        "messages": [
            "Tier 1 (Primary) is OPEN for this nationality",
            "No dominance concerns for this profession",
            "High priority score due to strategic sector bonus",
        ],
    }


def submit_request(nationality_id: int, profession_id: int, establishment_id: int, count: int):
    """Submit a quota request."""
    try:
        response = requests.post(
            f"{API_BASE}/api/v1/requests",
            json={
                "establishment_id": establishment_id,
                "nationality_id": nationality_id,
                "profession_id": profession_id,
                "requested_count": count,
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Demo response
    return {
        "request_id": 12345,
        "decision": "APPROVED",
        "approved_count": count,
        "queued_count": 0,
        "priority_score": 80,
        "tier_level": 1,
        "tier_status": "OPEN",
        "dominance_alert": None,
        "reason": f"APPROVED: Tier 1 OPEN, dominance OK. All {count} workers approved.",
        "alternatives": [],
    }


# Request form
st.markdown("### Submit New Request")
render_gold_accent()

col1, col2 = st.columns(2)

with col1:
    establishment = st.selectbox(
        "Establishment",
        options=list(ESTABLISHMENTS.keys()),
        format_func=lambda x: ESTABLISHMENTS[x],
    )
    
    nationality = st.selectbox(
        "Nationality",
        options=list(NATIONALITIES.keys()),
        format_func=lambda x: f"{x} - {NATIONALITIES[x]}",
    )

with col2:
    profession = st.selectbox(
        "Profession",
        options=list(PROFESSIONS.keys()),
        format_func=lambda x: PROFESSIONS[x],
    )
    
    count = st.number_input(
        "Number of Workers",
        min_value=1,
        max_value=500,
        value=5,
        help="Maximum 500 per request"
    )

# Eligibility check section
st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)
st.markdown("### Eligibility Check")
render_gold_accent()

if st.button("Check Eligibility", type="secondary"):
    with st.spinner("Checking eligibility..."):
        result = check_eligibility(
            nationality_id=list(NATIONALITIES.keys()).index(nationality) + 1,
            profession_id=profession,
            establishment_id=establishment,
            count=count,
        )
    
    st.session_state.eligibility_result = result

# Display eligibility result
if "eligibility_result" in st.session_state:
    result = st.session_state.eligibility_result
    
    elig_cols = st.columns([1, 1, 1, 1])
    
    with elig_cols[0]:
        render_status_card(
            title="Eligibility",
            status="OPEN" if result["is_eligible"] else "CLOSED",
            description="Request can proceed" if result["is_eligible"] else "Not eligible",
        )
    
    with elig_cols[1]:
        render_status_card(
            title=f"Tier {result['tier_level']}",
            status=result["tier_status"],
            description=result["tier_name"],
        )
    
    with elig_cols[2]:
        render_metric_card(
            label="Priority Score",
            value=result["priority_score"],
            icon="⭐"
        )
    
    with elig_cols[3]:
        outcome_status = {
            "APPROVED": "OPEN",
            "PARTIAL": "RATIONED",
            "QUEUED": "LIMITED",
            "BLOCKED": "CLOSED",
        }
        render_status_card(
            title="Expected Outcome",
            status=outcome_status.get(result["estimated_outcome"], "CLOSED"),
            description=result["estimated_outcome"],
        )
    
    # Messages
    st.markdown("#### Assessment")
    for msg in result["messages"]:
        if "CRITICAL" in msg or "blocked" in msg.lower():
            render_alert_box("critical", "Warning", msg)
        elif "HIGH" in msg or "partial" in msg.lower():
            render_alert_box("high", "Note", msg)
        elif "WATCH" in msg:
            render_alert_box("watch", "Info", msg)
        else:
            st.info(msg)
    
    # Dominance alert
    if result.get("dominance_alert"):
        st.markdown("<br>", unsafe_allow_html=True)
        render_alert_box(
            result["dominance_alert"],
            "Dominance Alert",
            f"This nationality has elevated concentration in the selected profession."
        )

# Submit section
st.markdown("<hr style='margin: 2rem 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)
st.markdown("### Submit Request")
render_gold_accent()

can_submit = st.session_state.get("eligibility_result", {}).get("is_eligible", False)

if not can_submit:
    render_info_box(
        "Please check eligibility before submitting. "
        "The system will validate your request against current caps and tier status."
    )

submit_col1, submit_col2 = st.columns([3, 1])

with submit_col1:
    st.markdown(f"""
    **Summary:**
    - Establishment: {ESTABLISHMENTS[establishment]}
    - Nationality: {nationality} - {NATIONALITIES[nationality]}
    - Profession: {PROFESSIONS[profession]}
    - Workers: {count}
    """)

with submit_col2:
    if st.button(
        "Submit Request", 
        type="primary", 
        disabled=not can_submit,
        use_container_width=True
    ):
        with st.spinner("Processing request..."):
            decision = submit_request(
                nationality_id=list(NATIONALITIES.keys()).index(nationality) + 1,
                profession_id=profession,
                establishment_id=establishment,
                count=count,
            )
        
        st.session_state.last_decision = decision
        
        if decision["decision"] == "APPROVED":
            st.success(f"✅ Request APPROVED! {decision['approved_count']} workers approved.")
            st.balloons()
        elif decision["decision"] == "PARTIAL":
            st.warning(f"⚠️ PARTIAL approval: {decision['approved_count']} of {count} workers approved.")
        elif decision["decision"] == "QUEUED":
            st.info(f"⏳ Request QUEUED for auto-processing when capacity opens.")
        elif decision["decision"] == "BLOCKED":
            st.error(f"🚫 Request BLOCKED: {decision['reason']}")
        else:
            st.error(f"❌ Request REJECTED: {decision['reason']}")

# Display last decision details
if "last_decision" in st.session_state:
    decision = st.session_state.last_decision
    
    st.markdown("#### Decision Details")
    
    dec_cols = st.columns(4)
    
    with dec_cols[0]:
        st.metric("Request ID", decision["request_id"])
    with dec_cols[1]:
        st.metric("Approved", decision["approved_count"])
    with dec_cols[2]:
        st.metric("Queued", decision.get("queued_count", 0))
    with dec_cols[3]:
        st.metric("Priority", decision["priority_score"])
    
    st.markdown("**Reason:**")
    st.info(decision["reason"])
    
    if decision.get("alternatives"):
        st.markdown("**Alternatives:**")
        for alt in decision["alternatives"]:
            st.markdown(f"- {alt}")
