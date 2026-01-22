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


# =============================================================================
# V4 COMPONENTS - QVC Constraint, Growth Direction, Formula Breakdown
# =============================================================================

def render_qvc_constraint_card(
    is_constrained: bool,
    desired_cap: int,
    max_achievable: int,
    net_qvc_capacity: int
):
    """
    Render QVC constraint status card.
    
    Shows whether the desired cap exceeds QVC processing capacity.
    
    Args:
        is_constrained: True if desired > max achievable
        desired_cap: What was calculated before constraint
        max_achievable: Stock + Net QVC capacity
        net_qvc_capacity: QVC Annual - Outflow
    """
    if is_constrained:
        gap = desired_cap - max_achievable
        bg_color = "linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%)"
        border_color = COLORS["error"]
        icon = "⚠️"
        status = "QVC CONSTRAINED"
        status_color = COLORS["error"]
        message = f"Desired cap exceeds QVC capacity by {gap:,} workers"
    else:
        bg_color = "linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)"
        border_color = COLORS["success"]
        icon = "✓"
        status = "Within QVC Capacity"
        status_color = COLORS["success"]
        message = "QVC can process all required workers"
    
    st.markdown(f"""
    <div style="
        background: {bg_color};
        border-radius: 12px;
        padding: 1.25rem;
        border-left: 4px solid {border_color};
        margin: 1rem 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 1.1rem; font-weight: 700; color: {status_color};">
                    {icon} {status}
                </div>
                <div style="font-size: 0.9rem; color: {COLORS['text_light']}; margin-top: 0.25rem;">
                    {message}
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.85rem; color: {COLORS['text_light']};">Net QVC Capacity</div>
                <div style="font-size: 1.25rem; font-weight: 700; color: {COLORS['primary']};">
                    {net_qvc_capacity:,}
                </div>
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid rgba(0,0,0,0.1);">
            <div style="text-align: center;">
                <div style="font-size: 0.75rem; color: {COLORS['text_light']};">Desired Cap</div>
                <div style="font-size: 1rem; font-weight: 600;">{desired_cap:,}</div>
            </div>
            <div style="font-size: 1.5rem; color: {COLORS['text_light']};">→</div>
            <div style="text-align: center;">
                <div style="font-size: 0.75rem; color: {COLORS['text_light']};">Max Achievable</div>
                <div style="font-size: 1rem; font-weight: 600; color: {border_color};">{max_achievable:,}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_growth_direction_card(
    direction: str,
    joiners: int,
    outflow: int,
    demand_basis: str
):
    """
    Render growth direction indicator with demand basis.
    
    Args:
        direction: "POSITIVE" or "NEGATIVE"
        joiners: Average annual joiners
        outflow: Average annual outflow
        demand_basis: "Joiners" or "Outflow"
    """
    if direction == "POSITIVE":
        icon = "📈"
        color = COLORS["success"]
        bg_color = "#E8F5E9"
    else:
        icon = "📉"
        color = COLORS["warning"]
        bg_color = "#FFF8E1"
    
    # Highlight which basis is being used
    joiners_style = f"font-weight: 700; color: {COLORS['success']};" if demand_basis == "Joiners" else f"color: {COLORS['text_light']};"
    outflow_style = f"font-weight: 700; color: {COLORS['warning']};" if demand_basis == "Outflow" else f"color: {COLORS['text_light']};"
    
    st.markdown(f"""
    <div style="
        background: {bg_color};
        border-radius: 12px;
        padding: 1rem;
        border-left: 4px solid {color};
    ">
        <div style="font-size: 0.85rem; color: {COLORS['text_light']}; text-transform: uppercase;">
            Growth Direction
        </div>
        <div style="font-size: 1.25rem; font-weight: 700; color: {color}; margin: 0.25rem 0;">
            {icon} {direction}
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 0.75rem; padding-top: 0.5rem; border-top: 1px solid rgba(0,0,0,0.1);">
            <div>
                <div style="font-size: 0.75rem; color: {COLORS['text_light']};">Avg Joiners/yr</div>
                <div style="{joiners_style}">{joiners:,}</div>
            </div>
            <div style="text-align: center; color: {COLORS['text_light']};">vs</div>
            <div style="text-align: right;">
                <div style="font-size: 0.75rem; color: {COLORS['text_light']};">Avg Outflow/yr</div>
                <div style="{outflow_style}">{outflow:,}</div>
            </div>
        </div>
        <div style="margin-top: 0.5rem; font-size: 0.85rem;">
            <span style="color: {COLORS['text_light']};">Demand Basis:</span>
            <span style="font-weight: 600; color: {color};"> {demand_basis}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_cap_formula_breakdown(
    stock: int,
    demand_basis: str,
    demand_value: int,
    buffer_pct: float,
    buffer_value: int,
    desired_cap: int,
    qvc_annual: int = None,
    net_qvc: int = None,
    max_achievable: int = None,
    recommended_cap: int = None,
    is_constrained: bool = False,
    country_type: str = "QVC"
):
    """
    Render step-by-step v4 formula calculation breakdown.
    
    Args:
        stock: Current stock
        demand_basis: "Joiners", "Outflow", or "Frozen"
        demand_value: The demand value used
        buffer_pct: Buffer percentage (0.10 = 10%)
        buffer_value: Calculated buffer value
        desired_cap: Stock + Demand + Buffer
        qvc_annual: QVC annual capacity (QVC countries only)
        net_qvc: Net QVC capacity (QVC countries only)
        max_achievable: Max achievable cap (QVC countries only)
        recommended_cap: Final recommended cap
        is_constrained: Whether QVC constraint is active
        country_type: "QVC", "OUTFLOW_BASED", or "STANDARD_NON_QVC"
    """
    # Format buffer as percentage
    buffer_pct_str = f"{buffer_pct * 100:.0f}%"
    
    # Determine final cap color
    final_color = COLORS["error"] if is_constrained else COLORS["success"]
    
    if country_type == "OUTFLOW_BASED":
        # Simplified display for outflow-based (frozen)
        st.markdown(f"""
        <div style="
            background: #FFF8E1;
            border-radius: 12px;
            padding: 1.25rem;
            border: 2px solid #FFA000;
            font-family: 'Courier New', monospace;
        ">
            <div style="font-weight: 700; color: {COLORS['primary']}; margin-bottom: 1rem; font-family: inherit;">
                📋 Cap Calculation (Outflow-Based)
            </div>
            <div style="color: {COLORS['text']}; line-height: 1.8;">
                <div>Current Stock:     <span style="color: {COLORS['primary']}; font-weight: 600;">{stock:>12,}</span></div>
                <div style="border-top: 1px dashed #ccc; margin: 0.5rem 0;"></div>
                <div style="font-weight: 700;">Recommended Cap:   <span style="color: #E65100; font-weight: 700;">{recommended_cap:>12,}</span> (FROZEN)</div>
            </div>
            <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid rgba(0,0,0,0.1); font-family: sans-serif; font-size: 0.85rem; color: {COLORS['text_light']};">
                Cap frozen at stock. Monthly allocation based on outflow.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Full QVC or Standard formula display
        qvc_section = ""
        if country_type == "QVC" and qvc_annual is not None:
            constraint_note = "(ACTIVE)" if is_constrained else "(not active)"
            qvc_section = f"""
            <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px dashed #ccc;">
                <div style="color: {COLORS['text_light']}; font-size: 0.85rem; margin-bottom: 0.5rem;">QVC Constraint:</div>
                <div>QVC Annual:        <span style="color: {COLORS['text']};">{qvc_annual:>12,}</span></div>
                <div>- Outflow:         <span style="color: {COLORS['text']};">{demand_value if demand_basis == 'Outflow' else net_qvc + qvc_annual - (stock + net_qvc) if net_qvc else 0:>12,}</span></div>
                <div>= Net QVC:         <span style="color: {COLORS['primary']}; font-weight: 600;">{net_qvc:>12,}</span></div>
                <div>Max Achievable:    <span style="color: {COLORS['text']};">{max_achievable:>12,}</span></div>
                <div style="font-size: 0.85rem; color: {COLORS['text_light']}; margin-top: 0.25rem;">
                    Constraint: {constraint_note}
                </div>
            </div>
            """
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #F8F5F0 0%, #FFFFFF 100%);
            border-radius: 12px;
            padding: 1.25rem;
            border: 2px solid {COLORS['secondary']};
            font-family: 'Courier New', monospace;
        ">
            <div style="font-weight: 700; color: {COLORS['primary']}; margin-bottom: 1rem; font-family: inherit;">
                📐 Cap Calculation (v4 Formula)
            </div>
            <div style="color: {COLORS['text']}; line-height: 1.8;">
                <div>Stock:             <span style="color: {COLORS['primary']}; font-weight: 600;">{stock:>12,}</span></div>
                <div>+ {demand_basis}:{' ' * (14 - len(demand_basis))}<span style="color: {COLORS['text']};">{demand_value:>12,}</span></div>
                <div>+ Buffer ({buffer_pct_str}):{' ' * (8 - len(buffer_pct_str))}<span style="color: {COLORS['text']};">{buffer_value:>12,}</span></div>
                <div style="border-top: 1px solid #ccc; margin: 0.25rem 0;"></div>
                <div>= Desired Cap:     <span style="color: {COLORS['text']};">{desired_cap:>12,}</span></div>
            </div>
            {qvc_section}
            <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 2px solid {COLORS['primary']};">
                <div style="font-weight: 700; font-size: 1.1rem;">
                    RECOMMENDED:       <span style="color: {final_color}; font-weight: 700;">{recommended_cap:>12,}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
