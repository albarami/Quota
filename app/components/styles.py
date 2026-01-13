"""
Streamlit styling and theming.

Qatar government theme with professional styling.
"""

import streamlit as st


# Qatar Government Color Palette
COLORS = {
    "primary": "#7B1E3D",        # Qatar Maroon (Burgundy)
    "secondary": "#D4AF37",      # Gold accent
    "background": "#F8F5F0",     # Warm off-white
    "surface": "#FFFFFF",        # White
    "text": "#1A1A2E",          # Near black
    "text_light": "#5C5C7A",    # Gray text
    "success": "#2E7D4B",       # Green
    "warning": "#E6A700",       # Amber
    "error": "#C41E3A",         # Red
    "info": "#1976D2",          # Blue
    # Tier colors
    "tier1": "#7B1E3D",         # Primary (Maroon)
    "tier2": "#1976D2",         # Secondary (Blue)
    "tier3": "#5C5C7A",         # Minor (Gray)
    "tier4": "#A0A0A0",         # Unusual (Light gray)
    # Status colors
    "open": "#2E7D4B",
    "rationed": "#E6A700",
    "limited": "#E65100",
    "closed": "#C41E3A",
}


def apply_custom_css():
    """Apply custom CSS for the entire application."""
    st.markdown("""
    <style>
        /* Import Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Source+Sans+Pro:wght@300;400;600;700&display=swap');
        
        /* Root Variables */
        :root {
            --primary: #7B1E3D;
            --secondary: #D4AF37;
            --background: #F8F5F0;
            --surface: #FFFFFF;
            --text: #1A1A2E;
            --text-light: #5C5C7A;
            --success: #2E7D4B;
            --warning: #E6A700;
            --error: #C41E3A;
            --font-display: 'Playfair Display', Georgia, serif;
            --font-body: 'Source Sans Pro', -apple-system, sans-serif;
        }
        
        /* ============================================
           BASE FONT SIZE - Increased for readability
           ============================================ */
        html, body, [class*="st-"] {
            font-size: 16px !important;
        }
        
        /* Global Styles */
        .main {
            background-color: var(--background);
        }
        
        h1, h2, h3 {
            font-family: var(--font-display);
            color: var(--primary);
        }
        
        /* Increased heading sizes */
        h1 { font-size: 2.5rem !important; }
        h2 { font-size: 2rem !important; }
        h3 { font-size: 1.5rem !important; }
        
        body, p, span, div {
            font-family: var(--font-body);
        }
        
        /* ============================================
           SIDEBAR - Complete Overhaul for Readability
           ============================================ */
        
        /* Sidebar background */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #7B1E3D 0%, #5A1530 100%) !important;
        }
        
        /* Make ALL sidebar text white and larger */
        section[data-testid="stSidebar"] * {
            color: #FFFFFF !important;
        }
        
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] .stMarkdown span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stMetric label,
        section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
            color: rgba(255, 255, 255, 0.9) !important;
            font-size: 1rem !important;
        }
        
        /* Sidebar headings */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #FFFFFF !important;
            font-size: 1.4rem !important;
            font-weight: 600 !important;
            margin-top: 1.5rem !important;
        }
        
        /* Sidebar metric values - Gold accent */
        section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
            color: #D4AF37 !important;
            font-size: 2.2rem !important;
            font-weight: 700 !important;
        }
        
        /* Sidebar metric labels */
        section[data-testid="stSidebar"] [data-testid="stMetricLabel"] p {
            color: rgba(255, 255, 255, 0.85) !important;
            font-size: 0.95rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }
        
        /* ============================================
           SIDEBAR NAVIGATION - Critical Fix
           ============================================ */
        
        /* Navigation container */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            background: rgba(0, 0, 0, 0.15) !important;
            border-radius: 12px !important;
            padding: 0.75rem !important;
            margin-bottom: 1rem !important;
        }
        
        /* Navigation links - WHITE text on dark background */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] span,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li,
        section[data-testid="stSidebar"] nav a,
        section[data-testid="stSidebar"] ul li a {
            color: #FFFFFF !important;
            font-size: 1.1rem !important;
            font-weight: 500 !important;
            padding: 0.75rem 1rem !important;
            display: block !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
            text-decoration: none !important;
        }
        
        /* Navigation hover state */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover,
        section[data-testid="stSidebar"] nav a:hover {
            background: rgba(255, 255, 255, 0.15) !important;
            color: #D4AF37 !important;
        }
        
        /* Active/selected navigation item */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] [aria-selected="true"],
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] .st-emotion-cache-1rtdyuf {
            background: rgba(212, 175, 55, 0.2) !important;
            border-left: 3px solid #D4AF37 !important;
        }
        
        /* Fix for any black text in sidebar */
        section[data-testid="stSidebar"] [style*="color: rgb(0, 0, 0)"],
        section[data-testid="stSidebar"] [style*="color: black"],
        section[data-testid="stSidebar"] [style*="color:#000"] {
            color: #FFFFFF !important;
        }
        
        /* Sidebar divider */
        section[data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.2) !important;
            margin: 1.5rem 0 !important;
        }
        
        /* ============================================
           HEADER STYLING
           ============================================ */
        .main-header {
            background: linear-gradient(135deg, var(--primary) 0%, #5A1530 100%);
            color: white;
            padding: 2.5rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(123, 30, 61, 0.2);
        }
        
        .main-header h1 {
            color: white !important;
            font-size: 2.8rem !important;
            margin: 0;
            line-height: 1.2;
        }
        
        .main-header p {
            color: rgba(255, 255, 255, 0.9) !important;
            margin: 0.75rem 0 0 0;
            font-size: 1.2rem !important;
        }
        
        /* ============================================
           METRIC CARDS - Enhanced
           ============================================ */
        .metric-card {
            background: white;
            border-radius: 16px;
            padding: 1.75rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            border-left: 5px solid var(--primary);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        }
        
        .metric-value {
            font-size: 2.8rem !important;
            font-weight: 700;
            color: var(--primary);
            line-height: 1.2;
        }
        
        .metric-label {
            font-size: 1rem !important;
            color: var(--text-light);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }
        
        /* ============================================
           STATUS BADGES - Larger
           ============================================ */
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.5rem 1rem;
            border-radius: 24px;
            font-size: 1rem !important;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .status-open {
            background: #E8F5E9;
            color: #2E7D4B;
        }
        
        .status-rationed {
            background: #FFF8E1;
            color: #E6A700;
        }
        
        .status-limited {
            background: #FFF3E0;
            color: #E65100;
        }
        
        .status-closed {
            background: #FFEBEE;
            color: #C41E3A;
        }
        
        /* ============================================
           TIER INDICATORS - Larger
           ============================================ */
        .tier-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            font-weight: 700;
            font-size: 1.1rem !important;
        }
        
        .tier-1 { background: #7B1E3D; color: white; }
        .tier-2 { background: #1976D2; color: white; }
        .tier-3 { background: #5C5C7A; color: white; }
        .tier-4 { background: #E0E0E0; color: #5C5C7A; }
        
        /* ============================================
           ALERT CARDS - Enhanced
           ============================================ */
        .alert-critical {
            background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
            border-left: 5px solid #C41E3A;
            border-radius: 12px;
            padding: 1.25rem;
        }
        
        .alert-high {
            background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
            border-left: 5px solid #E65100;
            border-radius: 12px;
            padding: 1.25rem;
        }
        
        .alert-watch {
            background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%);
            border-left: 5px solid #E6A700;
            border-radius: 12px;
            padding: 1.25rem;
        }
        
        /* ============================================
           DATA TABLES - Enhanced Readability
           ============================================ */
        .dataframe {
            font-family: var(--font-body);
            border-radius: 12px;
            overflow: hidden;
            font-size: 1rem !important;
        }
        
        .dataframe thead th {
            background: var(--primary);
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.95rem !important;
            letter-spacing: 0.5px;
            padding: 1rem !important;
        }
        
        .dataframe tbody td {
            padding: 0.875rem !important;
            font-size: 1rem !important;
        }
        
        .dataframe tbody tr:nth-child(even) {
            background: #F8F8FA;
        }
        
        /* ============================================
           BUTTONS - Enhanced
           ============================================ */
        .stButton > button {
            background: linear-gradient(135deg, var(--primary) 0%, #5A1530 100%);
            color: white !important;
            border: none;
            border-radius: 10px;
            padding: 0.875rem 2.5rem;
            font-size: 1rem !important;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            box-shadow: 0 6px 20px rgba(123, 30, 61, 0.35);
            transform: translateY(-2px);
        }
        
        /* ============================================
           PROGRESS BARS
           ============================================ */
        .utilization-bar {
            background: #E0E0E0;
            border-radius: 12px;
            height: 14px;
            overflow: hidden;
        }
        
        .utilization-fill {
            height: 100%;
            border-radius: 12px;
            transition: width 0.3s ease;
        }
        
        /* ============================================
           SELECT BOXES & INPUTS
           ============================================ */
        .stSelectbox > div > div {
            border-radius: 10px;
            font-size: 1rem !important;
        }
        
        .stSelectbox label {
            font-size: 1rem !important;
            font-weight: 500 !important;
        }
        
        .stNumberInput label,
        .stTextInput label {
            font-size: 1rem !important;
            font-weight: 500 !important;
        }
        
        /* ============================================
           INFO BOXES
           ============================================ */
        .info-box {
            background: #E3F2FD;
            border-left: 5px solid #1976D2;
            border-radius: 12px;
            padding: 1.25rem;
            margin: 1rem 0;
            font-size: 1rem !important;
        }
        
        /* ============================================
           GOLD ACCENT LINE
           ============================================ */
        .gold-accent {
            width: 80px;
            height: 5px;
            background: var(--secondary);
            border-radius: 3px;
            margin: 0.75rem 0 1.75rem 0;
        }
        
        /* ============================================
           CARDS CONTAINER
           ============================================ */
        .cards-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.25rem;
            margin: 1.25rem 0;
        }
        
        /* ============================================
           FOOTER
           ============================================ */
        .footer {
            text-align: center;
            padding: 2.5rem;
            color: var(--text-light);
            font-size: 1rem !important;
            border-top: 1px solid #E0E0E0;
            margin-top: 3rem;
        }
        
        /* ============================================
           STREAMLIT NATIVE ELEMENTS - Override defaults
           ============================================ */
        
        /* Metric component */
        [data-testid="stMetricValue"] {
            font-size: 2.5rem !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 1rem !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] button {
            font-size: 1rem !important;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            font-size: 1.1rem !important;
        }
        
        /* Radio buttons & checkboxes */
        .stRadio label,
        .stCheckbox label {
            font-size: 1rem !important;
        }
        
        /* Toast messages */
        .stToast {
            font-size: 1rem !important;
        }
    </style>
    """, unsafe_allow_html=True)


def render_header(title: str, subtitle: str = None):
    """Render the main page header."""
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f"""
    <div class="main-header">
        <h1>{title}</h1>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def render_metric(label: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Render a styled metric card."""
    delta_html = ""
    if delta:
        color = COLORS["success"] if delta_color == "normal" else COLORS["error"]
        delta_html = f'<div style="color: {color}; font-size: 0.9rem;">{delta}</div>'
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """Render a status badge HTML."""
    status_lower = status.lower()
    return f'<span class="status-badge status-{status_lower}">{status}</span>'


def render_tier_badge(tier: int) -> str:
    """Render a tier badge HTML."""
    return f'<span class="tier-badge tier-{tier}">{tier}</span>'


def render_gold_accent():
    """Render a gold accent line."""
    st.markdown('<div class="gold-accent"></div>', unsafe_allow_html=True)


def render_alert_box(level: str, title: str, message: str):
    """Render an alert box."""
    st.markdown(f"""
    <div class="alert-{level.lower()}">
        <strong>{title}</strong>
        <p style="margin: 0.5rem 0 0 0;">{message}</p>
    </div>
    """, unsafe_allow_html=True)


def render_info_box(message: str):
    """Render an info box."""
    st.markdown(f"""
    <div class="info-box">
        {message}
    </div>
    """, unsafe_allow_html=True)
