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
        
        /* Global Styles */
        .main {
            background-color: var(--background);
        }
        
        h1, h2, h3 {
            font-family: var(--font-display);
            color: var(--primary);
        }
        
        body, p, span, div {
            font-family: var(--font-body);
        }
        
        /* Header Styling */
        .main-header {
            background: linear-gradient(135deg, var(--primary) 0%, #5A1530 100%);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(123, 30, 61, 0.15);
        }
        
        .main-header h1 {
            color: white;
            font-size: 2.5rem;
            margin: 0;
        }
        
        .main-header p {
            color: rgba(255, 255, 255, 0.85);
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
        }
        
        /* Metric Cards */
        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            border-left: 4px solid var(--primary);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary);
            line-height: 1.2;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: var(--text-light);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Status Badges */
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.35rem 0.85rem;
            border-radius: 20px;
            font-size: 0.85rem;
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
        
        /* Tier Indicators */
        .tier-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            font-weight: 700;
            font-size: 0.9rem;
        }
        
        .tier-1 { background: #7B1E3D; color: white; }
        .tier-2 { background: #1976D2; color: white; }
        .tier-3 { background: #5C5C7A; color: white; }
        .tier-4 { background: #E0E0E0; color: #5C5C7A; }
        
        /* Alert Cards */
        .alert-critical {
            background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
            border-left: 4px solid #C41E3A;
            border-radius: 8px;
            padding: 1rem;
        }
        
        .alert-high {
            background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
            border-left: 4px solid #E65100;
            border-radius: 8px;
            padding: 1rem;
        }
        
        .alert-watch {
            background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%);
            border-left: 4px solid #E6A700;
            border-radius: 8px;
            padding: 1rem;
        }
        
        /* Data Tables */
        .dataframe {
            font-family: var(--font-body);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .dataframe thead th {
            background: var(--primary);
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.5px;
        }
        
        .dataframe tbody tr:nth-child(even) {
            background: #F8F8FA;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, var(--primary) 0%, #5A1530 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            box-shadow: 0 4px 12px rgba(123, 30, 61, 0.3);
            transform: translateY(-1px);
        }
        
        /* Progress Bars */
        .utilization-bar {
            background: #E0E0E0;
            border-radius: 10px;
            height: 12px;
            overflow: hidden;
        }
        
        .utilization-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #7B1E3D 0%, #5A1530 100%);
        }
        
        section[data-testid="stSidebar"] .stMarkdown {
            color: white;
        }
        
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: white;
        }
        
        /* Select boxes */
        .stSelectbox > div > div {
            border-radius: 8px;
        }
        
        /* Info boxes */
        .info-box {
            background: #E3F2FD;
            border-left: 4px solid #1976D2;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        /* Gold accent line */
        .gold-accent {
            width: 60px;
            height: 4px;
            background: var(--secondary);
            border-radius: 2px;
            margin: 0.5rem 0 1.5rem 0;
        }
        
        /* Cards container */
        .cards-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-light);
            font-size: 0.85rem;
            border-top: 1px solid #E0E0E0;
            margin-top: 3rem;
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
