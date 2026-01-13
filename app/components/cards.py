"""
Metric cards and status cards for the dashboard.

Provides visually rich card components for displaying key metrics.
"""

import streamlit as st

from app.components.styles import COLORS


def render_metric_card(
    label: str,
    value: str | int | float,
    delta: str = None,
    delta_color: str = "normal",
    icon: str = None
):
    """
    Render a styled metric card.
    
    Args:
        label: Metric label
        value: Metric value
        delta: Optional change indicator
        delta_color: "normal" for green, "inverse" for red
        icon: Optional emoji/icon
    """
    icon_html = f'<span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>' if icon else ""
    
    delta_html = ""
    if delta:
        color = COLORS["success"] if delta_color == "normal" else COLORS["error"]
        delta_html = f'<div style="color: {color}; font-size: 0.9rem; margin-top: 0.25rem;">{delta}</div>'
    
    # Format value
    if isinstance(value, (int, float)):
        value = f"{value:,.0f}"
    
    st.markdown(f"""
    <div style="
        background: white;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        border-left: 4px solid {COLORS['primary']};
        transition: transform 0.2s ease;
    ">
        <div style="color: {COLORS['text_light']}; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px;">
            {icon_html}{label}
        </div>
        <div style="font-size: 2rem; font-weight: 700; color: {COLORS['primary']}; line-height: 1.3;">
            {value}
        </div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_status_card(
    title: str,
    status: str,
    description: str = None,
    show_icon: bool = True
):
    """
    Render a status indicator card.
    
    Args:
        title: Card title
        status: Status value (OPEN, RATIONED, LIMITED, CLOSED)
        description: Optional description
        show_icon: Whether to show status icon
    """
    # Status styling
    status_config = {
        "OPEN": {
            "bg": "#E8F5E9",
            "color": COLORS["open"],
            "icon": "🟢",
            "border": COLORS["open"],
        },
        "RATIONED": {
            "bg": "#FFF8E1",
            "color": COLORS["rationed"],
            "icon": "🟡",
            "border": COLORS["rationed"],
        },
        "LIMITED": {
            "bg": "#FFF3E0",
            "color": COLORS["limited"],
            "icon": "🟠",
            "border": COLORS["limited"],
        },
        "CLOSED": {
            "bg": "#FFEBEE",
            "color": COLORS["closed"],
            "icon": "🔴",
            "border": COLORS["closed"],
        },
    }
    
    config = status_config.get(status.upper(), status_config["CLOSED"])
    icon = config["icon"] if show_icon else ""
    desc_html = f'<div style="font-size: 0.85rem; color: {COLORS["text_light"]}; margin-top: 0.5rem;">{description}</div>' if description else ""
    
    st.markdown(f"""
    <div style="
        background: {config['bg']};
        border-radius: 12px;
        padding: 1.25rem;
        border-left: 4px solid {config['border']};
    ">
        <div style="font-size: 0.9rem; color: {COLORS['text_light']}; text-transform: uppercase;">
            {title}
        </div>
        <div style="font-size: 1.5rem; font-weight: 700; color: {config['color']}; margin-top: 0.25rem;">
            {icon} {status}
        </div>
        {desc_html}
    </div>
    """, unsafe_allow_html=True)


def render_tier_card(
    tier_level: int,
    tier_name: str,
    status: str,
    capacity: int,
    share_pct: float = None
):
    """
    Render a tier status card.
    
    Args:
        tier_level: 1-4
        tier_name: Primary, Secondary, Minor, Unusual
        status: OPEN, RATIONED, LIMITED, CLOSED
        capacity: Available capacity
        share_pct: Request share percentage
    """
    # Tier colors
    tier_colors = {
        1: COLORS["tier1"],
        2: COLORS["tier2"],
        3: COLORS["tier3"],
        4: COLORS["tier4"],
    }
    
    # Status colors
    status_colors = {
        "OPEN": COLORS["open"],
        "RATIONED": COLORS["rationed"],
        "LIMITED": COLORS["limited"],
        "CLOSED": COLORS["closed"],
    }
    
    tier_color = tier_colors.get(tier_level, COLORS["tier4"])
    status_color = status_colors.get(status.upper(), COLORS["closed"])
    
    share_html = ""
    if share_pct is not None:
        share_html = f'<div style="font-size: 0.85rem; color: {COLORS["text_light"]};">{share_pct:.1%} of requests</div>'
    
    st.markdown(f"""
    <div style="
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
        border-top: 4px solid {tier_color};
        text-align: center;
    ">
        <div style="
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: {tier_color};
            color: white;
            font-weight: 700;
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
        ">{tier_level}</div>
        <div style="font-weight: 600; color: {COLORS['text']};">{tier_name}</div>
        <div style="
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            background: {status_color}20;
            color: {status_color};
            font-weight: 600;
            font-size: 0.85rem;
            margin: 0.5rem 0;
        ">{status}</div>
        <div style="font-size: 1.25rem; font-weight: 700; color: {COLORS['primary']};">
            {capacity:,} slots
        </div>
        {share_html}
    </div>
    """, unsafe_allow_html=True)


def render_alert_card(
    level: str,
    profession: str,
    share_pct: float,
    velocity: float,
    is_blocking: bool = False
):
    """
    Render a dominance alert card.
    
    Args:
        level: CRITICAL, HIGH, WATCH, OK
        profession: Profession name
        share_pct: Nationality share in profession
        velocity: Share change rate
        is_blocking: Whether this alert blocks approvals
    """
    # Alert styling
    alert_config = {
        "CRITICAL": {
            "bg": "linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%)",
            "border": COLORS["error"],
            "icon": "🚨",
            "title_color": COLORS["error"],
        },
        "HIGH": {
            "bg": "linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%)",
            "border": COLORS["limited"],
            "icon": "⚠️",
            "title_color": COLORS["limited"],
        },
        "WATCH": {
            "bg": "linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%)",
            "border": COLORS["warning"],
            "icon": "👁️",
            "title_color": COLORS["warning"],
        },
        "OK": {
            "bg": "#E8F5E9",
            "border": COLORS["success"],
            "icon": "✓",
            "title_color": COLORS["success"],
        },
    }
    
    config = alert_config.get(level.upper(), alert_config["WATCH"])
    
    blocking_html = ""
    if is_blocking:
        blocking_html = '<div style="color: #C41E3A; font-weight: 700; margin-top: 0.5rem;">⛔ BLOCKING NEW APPROVALS</div>'
    
    st.markdown(f"""
    <div style="
        background: {config['bg']};
        border-radius: 12px;
        padding: 1rem;
        border-left: 4px solid {config['border']};
        margin-bottom: 0.75rem;
    ">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div style="font-size: 0.85rem; color: {config['title_color']}; font-weight: 600;">
                    {config['icon']} {level}
                </div>
                <div style="font-weight: 600; color: {COLORS['text']}; margin-top: 0.25rem;">
                    {profession}
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.25rem; font-weight: 700; color: {config['title_color']};">
                    {share_pct:.1%}
                </div>
                <div style="font-size: 0.8rem; color: {COLORS['text_light']};">
                    {velocity:+.1%}/3yr
                </div>
            </div>
        </div>
        {blocking_html}
    </div>
    """, unsafe_allow_html=True)


def render_kpi_row(metrics: list[dict]):
    """
    Render a row of KPI metric cards.
    
    Args:
        metrics: List of dicts with label, value, delta, icon
    """
    cols = st.columns(len(metrics))
    for i, metric in enumerate(metrics):
        with cols[i]:
            render_metric_card(
                label=metric.get("label", ""),
                value=metric.get("value", 0),
                delta=metric.get("delta"),
                delta_color=metric.get("delta_color", "normal"),
                icon=metric.get("icon"),
            )


def render_utilization_bar(
    current: int,
    maximum: int,
    label: str = "Utilization"
):
    """
    Render a utilization progress bar.
    
    Args:
        current: Current value
        maximum: Maximum value
        label: Bar label
    """
    pct = (current / maximum * 100) if maximum > 0 else 0
    
    # Color based on utilization
    if pct >= 90:
        color = COLORS["error"]
    elif pct >= 70:
        color = COLORS["warning"]
    else:
        color = COLORS["success"]
    
    st.markdown(f"""
    <div style="margin: 0.5rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
            <span style="font-size: 0.85rem; color: {COLORS['text_light']};">{label}</span>
            <span style="font-size: 0.85rem; font-weight: 600; color: {COLORS['text']};">{pct:.1f}%</span>
        </div>
        <div style="background: #E0E0E0; border-radius: 10px; height: 10px; overflow: hidden;">
            <div style="
                width: {min(pct, 100)}%;
                height: 100%;
                background: {color};
                border-radius: 10px;
                transition: width 0.3s ease;
            "></div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 0.25rem;">
            <span style="font-size: 0.8rem; color: {COLORS['text_light']};">{current:,}</span>
            <span style="font-size: 0.8rem; color: {COLORS['text_light']};">{maximum:,}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
