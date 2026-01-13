"""
Plotly chart builders for the dashboard.

Creates consistent, styled charts for the Streamlit frontend.
"""

from typing import Any

import plotly.express as px
import plotly.graph_objects as go

from app.components.styles import COLORS


def create_headroom_gauge(
    current: int,
    maximum: int,
    title: str = "Headroom"
) -> go.Figure:
    """
    Create a gauge chart showing headroom utilization.
    
    Args:
        current: Current stock value
        maximum: Cap limit
        title: Chart title
    """
    utilization = (current / maximum * 100) if maximum > 0 else 0
    
    # Determine color based on utilization
    if utilization >= 90:
        bar_color = COLORS["error"]
    elif utilization >= 70:
        bar_color = COLORS["warning"]
    else:
        bar_color = COLORS["success"]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=utilization,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": title, "font": {"size": 18, "color": COLORS["text"]}},
        delta={"reference": 70, "increasing": {"color": COLORS["error"]}},
        number={"suffix": "%", "font": {"size": 36}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": COLORS["text"]},
            "bar": {"color": bar_color},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": COLORS["text_light"],
            "steps": [
                {"range": [0, 70], "color": "#E8F5E9"},
                {"range": [70, 90], "color": "#FFF8E1"},
                {"range": [90, 100], "color": "#FFEBEE"},
            ],
            "threshold": {
                "line": {"color": COLORS["error"], "width": 4},
                "thickness": 0.75,
                "value": 90,
            },
        },
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Source Sans Pro"},
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    
    return fig


def create_tier_bar_chart(tier_data: list[dict]) -> go.Figure:
    """
    Create a horizontal bar chart showing tier status.
    
    Args:
        tier_data: List of dicts with tier_level, capacity, status
    """
    tiers = [f"Tier {d['tier_level']}" for d in tier_data]
    capacities = [d.get("capacity", 0) for d in tier_data]
    statuses = [d.get("status", "CLOSED") for d in tier_data]
    
    # Color by status
    colors = []
    for status in statuses:
        if status == "OPEN":
            colors.append(COLORS["open"])
        elif status == "RATIONED":
            colors.append(COLORS["rationed"])
        elif status == "LIMITED":
            colors.append(COLORS["limited"])
        else:
            colors.append(COLORS["closed"])
    
    fig = go.Figure(go.Bar(
        y=tiers,
        x=capacities,
        orientation="h",
        marker_color=colors,
        text=statuses,
        textposition="inside",
        textfont={"color": "white", "size": 14, "family": "Source Sans Pro"},
    ))
    
    fig.update_layout(
        title={
            "text": "Tier Capacity Status",
            "font": {"size": 18, "color": COLORS["primary"]},
        },
        xaxis_title="Available Capacity",
        yaxis_title="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Source Sans Pro"},
        height=250,
        margin=dict(l=80, r=20, t=50, b=40),
    )
    
    return fig


def create_dominance_pie(nationality_data: list[dict], profession_name: str) -> go.Figure:
    """
    Create a pie chart showing nationality distribution in a profession.
    
    Args:
        nationality_data: List of dicts with nationality_code, count
        profession_name: Name of the profession
    """
    labels = [d["nationality_code"] for d in nationality_data]
    values = [d["count"] for d in nationality_data]
    
    # Use a color palette
    palette = [
        COLORS["primary"], COLORS["tier2"], COLORS["warning"],
        COLORS["success"], COLORS["info"], "#9C27B0", "#FF5722",
        "#795548", "#607D8B", "#E91E63", "#00BCD4"
    ]
    
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker_colors=palette[:len(labels)],
        textinfo="percent+label",
        textfont={"family": "Source Sans Pro", "size": 12},
        hovertemplate="<b>%{label}</b><br>Workers: %{value:,}<br>Share: %{percent}<extra></extra>",
    ))
    
    fig.update_layout(
        title={
            "text": f"Distribution: {profession_name}",
            "font": {"size": 16, "color": COLORS["primary"]},
        },
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Source Sans Pro"},
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=True,
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.2},
    )
    
    return fig


def create_queue_timeline(queue_data: list[dict]) -> go.Figure:
    """
    Create a timeline chart showing queue entries and expiry.
    
    Args:
        queue_data: List of queue entries with queued_date, expiry_date
    """
    import pandas as pd
    
    if not queue_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No items in queue",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font={"size": 16, "color": COLORS["text_light"]},
        )
        fig.update_layout(
            height=200,
            paper_bgcolor="rgba(0,0,0,0)",
        )
        return fig
    
    df = pd.DataFrame(queue_data)
    df["queued_date"] = pd.to_datetime(df["queued_date"])
    df["expiry_date"] = pd.to_datetime(df["expiry_date"])
    
    fig = go.Figure()
    
    # Add bars for each queue entry
    for i, row in df.iterrows():
        color = COLORS["warning"] if row.get("needs_confirmation") else COLORS["info"]
        fig.add_trace(go.Bar(
            x=[(row["expiry_date"] - row["queued_date"]).days],
            y=[f"Request {row['request_id']}"],
            orientation="h",
            marker_color=color,
            hovertemplate=(
                f"Request {row['request_id']}<br>"
                f"Queued: {row['queued_date'].strftime('%Y-%m-%d')}<br>"
                f"Expires: {row['expiry_date'].strftime('%Y-%m-%d')}<br>"
                f"Days left: {row.get('days_until_expiry', 'N/A')}"
                "<extra></extra>"
            ),
        ))
    
    fig.update_layout(
        title={
            "text": "Queue Timeline",
            "font": {"size": 16, "color": COLORS["primary"]},
        },
        xaxis_title="Days in Queue",
        yaxis_title="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Source Sans Pro"},
        height=max(200, len(queue_data) * 40),
        showlegend=False,
        barmode="overlay",
    )
    
    return fig


def create_outflow_projection(
    days: list[int],
    values: list[int],
    confidence_low: list[int],
    confidence_high: list[int]
) -> go.Figure:
    """
    Create a line chart showing outflow projections with confidence bands.
    """
    fig = go.Figure()
    
    # Confidence band
    fig.add_trace(go.Scatter(
        x=days + days[::-1],
        y=confidence_high + confidence_low[::-1],
        fill="toself",
        fillcolor=f"rgba(25, 118, 210, 0.2)",
        line={"color": "rgba(0,0,0,0)"},
        name="Confidence Band",
        showlegend=True,
    ))
    
    # Main projection line
    fig.add_trace(go.Scatter(
        x=days,
        y=values,
        mode="lines+markers",
        line={"color": COLORS["info"], "width": 3},
        marker={"size": 8},
        name="Projected Outflow",
    ))
    
    fig.update_layout(
        title={
            "text": "Projected Workforce Outflow",
            "font": {"size": 16, "color": COLORS["primary"]},
        },
        xaxis_title="Days",
        yaxis_title="Workers",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Source Sans Pro"},
        height=300,
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.3},
    )
    
    return fig


def create_request_history(request_data: list[dict]) -> go.Figure:
    """
    Create a stacked area chart showing request history by status.
    """
    import pandas as pd
    
    if not request_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No request history",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
        )
        return fig
    
    df = pd.DataFrame(request_data)
    df["month"] = pd.to_datetime(df["submitted_date"]).dt.to_period("M").astype(str)
    
    # Aggregate by month and status
    grouped = df.groupby(["month", "status"]).size().unstack(fill_value=0)
    
    fig = go.Figure()
    
    status_colors = {
        "APPROVED": COLORS["success"],
        "PARTIAL": COLORS["info"],
        "QUEUED": COLORS["warning"],
        "BLOCKED": COLORS["error"],
        "REJECTED": "#9E9E9E",
    }
    
    for status in grouped.columns:
        fig.add_trace(go.Scatter(
            x=grouped.index,
            y=grouped[status],
            mode="lines",
            stackgroup="one",
            name=status,
            line={"color": status_colors.get(status, "#888")},
        ))
    
    fig.update_layout(
        title={
            "text": "Request History by Status",
            "font": {"size": 16, "color": COLORS["primary"]},
        },
        xaxis_title="Month",
        yaxis_title="Requests",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Source Sans Pro"},
        height=300,
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.3},
    )
    
    return fig


def create_cap_recommendation_chart(
    current: int,
    conservative: int,
    moderate: int,
    flexible: int,
    recommended: int
) -> go.Figure:
    """
    Create a bar chart comparing cap options.
    """
    options = ["Current", "Conservative", "Moderate", "Flexible"]
    values = [current or 0, conservative, moderate, flexible]
    
    # Highlight recommended
    colors = []
    for i, opt in enumerate(options):
        if values[i] == recommended:
            colors.append(COLORS["secondary"])  # Gold for recommended
        elif opt == "Current":
            colors.append(COLORS["text_light"])
        else:
            colors.append(COLORS["primary"])
    
    fig = go.Figure(go.Bar(
        x=options,
        y=values,
        marker_color=colors,
        text=[f"{v:,}" for v in values],
        textposition="outside",
        textfont={"family": "Source Sans Pro", "size": 14},
    ))
    
    # Add annotation for recommended
    rec_idx = values.index(recommended) if recommended in values else 2
    fig.add_annotation(
        x=options[rec_idx],
        y=values[rec_idx],
        text="★ RECOMMENDED",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor=COLORS["secondary"],
        font={"size": 12, "color": COLORS["secondary"]},
        yshift=30,
    )
    
    fig.update_layout(
        title={
            "text": "Cap Options Comparison",
            "font": {"size": 16, "color": COLORS["primary"]},
        },
        xaxis_title="",
        yaxis_title="Cap Limit",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Source Sans Pro"},
        height=350,
        showlegend=False,
    )
    
    return fig
