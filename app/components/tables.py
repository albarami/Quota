"""
Styled data tables for the dashboard.

Provides formatted, interactive tables using Streamlit and pandas.
"""

import streamlit as st
import pandas as pd

from app.components.styles import COLORS


def render_nationality_table(data: list[dict]):
    """
    Render a styled table of nationalities with key metrics.
    
    Args:
        data: List of nationality data dicts
    """
    if not data:
        st.info("No nationality data available")
        return
    
    df = pd.DataFrame(data)
    
    # Format columns
    df["utilization"] = df["utilization_pct"].apply(lambda x: f"{x:.1%}")
    df["headroom"] = df["headroom"].apply(lambda x: f"{x:,}")
    df["stock"] = df["stock"].apply(lambda x: f"{x:,}")
    df["cap"] = df["cap"].apply(lambda x: f"{x:,}")
    
    # Select display columns
    display_df = df[["nationality_code", "cap", "stock", "headroom", "utilization"]]
    display_df.columns = ["Nationality", "Cap", "Stock", "Headroom", "Utilization"]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Nationality": st.column_config.TextColumn(
                "Nationality",
                help="Nationality code",
                width="small",
            ),
            "Cap": st.column_config.TextColumn(
                "Cap",
                help="Annual cap limit",
            ),
            "Stock": st.column_config.TextColumn(
                "Stock",
                help="Current workers",
            ),
            "Headroom": st.column_config.TextColumn(
                "Headroom",
                help="Available capacity",
            ),
            "Utilization": st.column_config.TextColumn(
                "Utilization",
                help="% of cap used",
            ),
        },
    )


def render_tier_table(tier_data: list[dict]):
    """
    Render a styled table of tier statuses.
    
    Args:
        tier_data: List of tier status dicts
    """
    if not tier_data:
        st.info("No tier data available")
        return
    
    df = pd.DataFrame(tier_data)
    
    # Format status with colors
    def format_status(status: str) -> str:
        colors = {
            "OPEN": "#2E7D4B",
            "RATIONED": "#E6A700",
            "LIMITED": "#E65100",
            "CLOSED": "#C41E3A",
        }
        return status
    
    df["status"] = df["status"].apply(format_status)
    df["capacity"] = df["capacity"].apply(lambda x: f"{x:,}")
    df["share"] = df.get("share_pct", pd.Series([0] * len(df))).apply(
        lambda x: f"{x:.1%}" if x else "N/A"
    )
    
    display_df = df[["tier_level", "tier_name", "status", "capacity"]]
    display_df.columns = ["Tier", "Name", "Status", "Capacity"]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


def render_queue_table(queue_data: list[dict]):
    """
    Render a styled table of queue entries.
    
    Args:
        queue_data: List of queue entry dicts
    """
    if not queue_data:
        st.info("Queue is empty")
        return
    
    df = pd.DataFrame(queue_data)
    
    # Format dates
    df["queued_date"] = pd.to_datetime(df["queued_date"]).dt.strftime("%Y-%m-%d")
    df["expiry_date"] = pd.to_datetime(df["expiry_date"]).dt.strftime("%Y-%m-%d")
    
    # Format confirmation status
    df["status"] = df.apply(
        lambda row: "⚠️ Needs Confirmation" if row.get("needs_confirmation") 
        else "✓ Confirmed" if row.get("is_confirmed") 
        else "Pending",
        axis=1
    )
    
    display_df = df[[
        "request_id", "tier_at_submission", "queued_date", 
        "expiry_date", "days_until_expiry", "status"
    ]]
    display_df.columns = ["Request ID", "Tier", "Queued", "Expires", "Days Left", "Status"]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


def render_alerts_table(alerts: list[dict]):
    """
    Render a styled table of dominance alerts.
    
    Args:
        alerts: List of alert dicts
    """
    if not alerts:
        st.success("No active alerts")
        return
    
    df = pd.DataFrame(alerts)
    
    # Format percentages
    df["share"] = df["share_pct"].apply(lambda x: f"{x:.1%}")
    df["velocity"] = df["velocity"].apply(lambda x: f"{x:+.1%}/3yr")
    
    # Format alert level with emoji
    level_emoji = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "WATCH": "🟡",
        "OK": "🟢",
    }
    df["level"] = df["alert_level"].apply(
        lambda x: f"{level_emoji.get(x, '')} {x}"
    )
    
    display_df = df[[
        "profession_name", "level", "share", "velocity", "nationality_count"
    ]]
    display_df.columns = ["Profession", "Alert Level", "Share", "Velocity", "Workers"]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


def render_request_table(requests: list[dict]):
    """
    Render a styled table of quota requests.
    
    Args:
        requests: List of request dicts
    """
    if not requests:
        st.info("No requests found")
        return
    
    df = pd.DataFrame(requests)
    
    # Format dates
    df["submitted"] = pd.to_datetime(df["submitted_date"]).dt.strftime("%Y-%m-%d %H:%M")
    
    # Format status with colors
    status_emoji = {
        "APPROVED": "✅",
        "PARTIAL": "⚠️",
        "QUEUED": "⏳",
        "BLOCKED": "🚫",
        "REJECTED": "❌",
        "WITHDRAWN": "↩️",
        "EXPIRED": "⌛",
    }
    df["status_fmt"] = df["status"].apply(
        lambda x: f"{status_emoji.get(x, '')} {x}"
    )
    
    # Format counts
    df["result"] = df.apply(
        lambda row: f"{row['approved_count']}/{row['requested_count']}"
        if row.get("approved_count") else f"0/{row['requested_count']}",
        axis=1
    )
    
    display_df = df[[
        "id", "nationality_code", "profession_name", 
        "result", "status_fmt", "priority_score", "submitted"
    ]]
    display_df.columns = [
        "ID", "Nationality", "Profession", 
        "Approved/Requested", "Status", "Priority", "Submitted"
    ]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


def render_cap_history_table(history: list[dict]):
    """
    Render a table of cap changes over time.
    
    Args:
        history: List of cap history dicts
    """
    if not history:
        st.info("No cap history available")
        return
    
    df = pd.DataFrame(history)
    
    # Format dates and values
    df["set_date"] = pd.to_datetime(df["set_date"]).dt.strftime("%Y-%m-%d")
    df["cap_limit"] = df["cap_limit"].apply(lambda x: f"{x:,}")
    df["change"] = df.apply(
        lambda row: f"+{row['cap_limit'] - row.get('previous_cap', row['cap_limit']):,}"
        if row.get("previous_cap") else "Initial",
        axis=1
    )
    
    display_df = df[["year", "cap_limit", "change", "set_by", "set_date"]]
    display_df.columns = ["Year", "Cap", "Change", "Set By", "Date"]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )
