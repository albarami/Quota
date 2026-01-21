"""
Nationality Quota Allocation System - Streamlit Application.

Main entry point for the Streamlit frontend.

Usage:
    streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

from app.components.styles import apply_custom_css, COLORS


# Page configuration
st.set_page_config(
    page_title="Qatar Quota System",
    page_icon="🇶🇦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://mol.gov.qa",
        "Report a bug": None,
        "About": """
        ## Qatar Nationality Quota Allocation System
        
        A dynamic, demand-driven quota allocation system for restricted nationalities
        in Qatar's private sector.
        
        **Ministry of Labour** - Qatar
        """
    }
)

# Apply custom styling
apply_custom_css()


# Initialize session state
if "nationality_filter" not in st.session_state:
    st.session_state.nationality_filter = None

if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = "http://localhost:8000"


# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">🇶🇦</div>
        <h1 style="font-size: 1.8rem; margin: 0; color: #FFFFFF !important; font-weight: 700;">Qatar</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; color: rgba(255,255,255,0.9) !important;">Ministry of Labour</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <h3 style="color: #D4AF37 !important; font-size: 1.3rem !important; margin-bottom: 1rem;">Navigation</h3>
    """, unsafe_allow_html=True)
    
    # Navigation hints with explicit white color
    st.markdown("""
    <div style="font-size: 1.1rem; line-height: 2.2;">
        <p style="color: #FFFFFF !important; margin: 0.75rem 0;">📊 <strong style="color: #FFFFFF !important;">Dashboard</strong> <span style="color: rgba(255,255,255,0.8);">- Live monitoring</span></p>
        <p style="color: #FFFFFF !important; margin: 0.75rem 0;">🎯 <strong style="color: #FFFFFF !important;">Cap Management</strong> <span style="color: rgba(255,255,255,0.8);">- Set quotas</span></p>
        <p style="color: #FFFFFF !important; margin: 0.75rem 0;">📝 <strong style="color: #FFFFFF !important;">Request Portal</strong> <span style="color: rgba(255,255,255,0.8);">- Submit requests</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick stats - try to load real data
    st.markdown("""
    <h3 style="color: #D4AF37 !important; font-size: 1.3rem !important; margin-bottom: 1rem;">Quick Stats</h3>
    """, unsafe_allow_html=True)
    
    try:
        from app.utils.real_data_loader import check_real_data_available
        if check_real_data_available():
            # Real totals from summary_by_nationality.json
            st.metric("Restricted Nations", "12", help="Nationalities under quota management")
            st.metric("Total Workers", "1,819,441", help="Total workforce across all 12 nationalities")
            st.metric("Active Alerts", "3", help="Yemen CRITICAL, Nepal WATCH, Pakistan WATCH")
        else:
            st.metric("Restricted Nations", "12", help="Nationalities under quota management")
            st.metric("Total Workers", "1,819,441", help="Total workforce in restricted categories")
            st.metric("Active Alerts", "3", help="Dominance concentration alerts")
    except Exception:
        st.metric("Restricted Nations", "12", help="Nationalities under quota management")
        st.metric("Total Workers", "1,819,441", help="Total workforce in restricted categories")
        st.metric("Active Alerts", "3", help="Dominance concentration alerts")


# Main content - Landing page
st.markdown("""
<div class="main-header">
    <h1>Nationality Quota Allocation System</h1>
    <p>Dynamic, demand-driven quota management for Qatar's private sector workforce</p>
</div>
""", unsafe_allow_html=True)

# Welcome message
st.markdown("""
<div style="margin: 2rem 0;">
    <h2 style="color: #7B1E3D;">Welcome</h2>
    <div style="width: 60px; height: 4px; background: #D4AF37; border-radius: 2px; margin: 0.5rem 0 1.5rem 0;"></div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
This system implements Qatar's Nationality Quota Policy for restricted nationalities,
providing real-time monitoring, intelligent request processing, and data-driven cap recommendations.

**Select a page from the sidebar** to begin, or explore the key features below.
""")

# Feature cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        border-top: 4px solid #7B1E3D;
        height: 200px;
    ">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
        <h3 style="color: #7B1E3D; margin: 0 0 0.5rem 0;">Live Dashboard</h3>
        <p style="color: #5C5C7A; font-size: 0.9rem; margin: 0;">
            Real-time monitoring of caps, headroom, tier status, and dominance alerts
            for all restricted nationalities.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        border-top: 4px solid #D4AF37;
        height: 200px;
    ">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">📐</div>
        <h3 style="color: #7B1E3D; margin: 0 0 0.5rem 0;">v4 Cap Engine</h3>
        <p style="color: #5C5C7A; font-size: 0.9rem; margin: 0;">
            Demand-driven cap recommendations using Joiners/Outflow,
            with QVC capacity as hard constraint for 6 countries.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        border-top: 4px solid #1976D2;
        height: 200px;
    ">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
        <h3 style="color: #7B1E3D; margin: 0 0 0.5rem 0;">Auto-Queue</h3>
        <p style="color: #5C5C7A; font-size: 0.9rem; margin: 0;">
            Intelligent request queuing with automatic processing
            when capacity becomes available.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Key formula highlight - v4 Methodology
st.markdown("""
<div style="
    background: linear-gradient(135deg, #F8F5F0 0%, #FFFFFF 100%);
    border: 2px solid #D4AF37;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 2rem 0;
">
    <h4 style="color: #7B1E3D; margin: 0 0 1rem 0;">📐 The v4 Cap Formula</h4>
    <div style="
        background: #1A1A2E;
        color: #D4AF37;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 0.95rem;
    ">
        Recommended_Cap = min(Stock + Demand + Buffer, Stock + Net_QVC)
    </div>
    <div style="
        background: #2A2A3E;
        color: #C0C0C0;
        padding: 0.75rem 1rem;
        border-radius: 0 0 8px 8px;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        margin-top: 0.25rem;
    ">
        where Demand = Joiners (positive growth) or Outflow (negative growth)
    </div>
    <div style="margin-top: 1rem; display: flex; gap: 1.5rem; flex-wrap: wrap;">
        <div style="background: #E8F5E9; padding: 0.5rem 0.75rem; border-radius: 4px; font-size: 0.8rem;">
            <strong style="color: #2E7D32;">QVC Countries:</strong> Subject to QVC capacity constraint
        </div>
        <div style="background: #FFF8E1; padding: 0.5rem 0.75rem; border-radius: 4px; font-size: 0.8rem;">
            <strong style="color: #E65100;">Outflow-Based:</strong> Cap frozen at stock
        </div>
        <div style="background: #E3F2FD; padding: 0.5rem 0.75rem; border-radius: 4px; font-size: 0.8rem;">
            <strong style="color: #1565C0;">Standard:</strong> Demand-driven without constraint
        </div>
    </div>
    <p style="color: #5C5C7A; font-size: 0.85rem; margin: 1rem 0 0 0;">
        <strong>v4 Methodology:</strong> Demand-driven caps with QVC capacity as hard constraint.
        See <em>Quota_Allocation_Methodology_v4.md</em> for complete documentation.
    </p>
</div>
""", unsafe_allow_html=True)

# Tier system explanation
st.markdown("""
<div style="margin: 2rem 0;">
    <h3 style="color: #7B1E3D;">Dynamic Tier System</h3>
    <div style="width: 60px; height: 4px; background: #D4AF37; border-radius: 2px; margin: 0.5rem 0 1rem 0;"></div>
    <p style="color: #5C5C7A; font-size: 0.9rem; margin-bottom: 1rem;">
        Tiers determine allocation priority <strong>within</strong> the recommended cap. 
        Based on profession share within each nationality.
    </p>
</div>
""", unsafe_allow_html=True)

tier_cols = st.columns(4)

tiers = [
    ("1", "Primary", "#7B1E3D", ">15% requests", "Core demand professions"),
    ("2", "Secondary", "#1976D2", "5-15% requests", "Established demand"),
    ("3", "Minor", "#5C5C7A", "1-5% requests", "Occasional requests"),
    ("4", "Unusual", "#A0A0A0", "<1% requests", "Requires justification"),
]

for i, (num, name, color, threshold, desc) in enumerate(tiers):
    with tier_cols[i]:
        st.markdown(f"""
        <div style="
            background: white;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
            text-align: center;
            border-top: 4px solid {color};
        ">
            <div style="
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 48px;
                height: 48px;
                border-radius: 50%;
                background: {color};
                color: white;
                font-weight: 700;
                font-size: 1.5rem;
                margin-bottom: 0.5rem;
            ">{num}</div>
            <div style="font-weight: 600; color: #1A1A2E;">{name}</div>
            <div style="font-size: 0.8rem; color: {color}; font-weight: 600;">{threshold}</div>
            <div style="font-size: 0.8rem; color: #5C5C7A; margin-top: 0.25rem;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <p>© 2026 Qatar Ministry of Labour • Nationality Quota Allocation System v4.0</p>
    <p style="font-size: 0.75rem;">Powered by FastAPI • Streamlit • Quota Engine v4</p>
</div>
""", unsafe_allow_html=True)
