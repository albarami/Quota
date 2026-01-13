"""
UI Components package.

Exports all styling, charts, tables, and cards.
"""

from app.components.styles import (
    COLORS,
    apply_custom_css,
    render_header,
    render_metric,
    render_status_badge,
    render_tier_badge,
    render_gold_accent,
    render_alert_box,
    render_info_box,
)

from app.components.charts import (
    create_headroom_gauge,
    create_tier_bar_chart,
    create_dominance_pie,
    create_queue_timeline,
    create_outflow_projection,
    create_request_history,
    create_cap_recommendation_chart,
)

from app.components.tables import (
    render_nationality_table,
    render_tier_table,
    render_queue_table,
    render_alerts_table,
    render_request_table,
    render_cap_history_table,
)

from app.components.cards import (
    render_metric_card,
    render_status_card,
    render_tier_card,
    render_alert_card,
    render_kpi_row,
    render_utilization_bar,
)

__all__ = [
    # Styles
    "COLORS",
    "apply_custom_css",
    "render_header",
    "render_metric",
    "render_status_badge",
    "render_tier_badge",
    "render_gold_accent",
    "render_alert_box",
    "render_info_box",
    # Charts
    "create_headroom_gauge",
    "create_tier_bar_chart",
    "create_dominance_pie",
    "create_queue_timeline",
    "create_outflow_projection",
    "create_request_history",
    "create_cap_recommendation_chart",
    # Tables
    "render_nationality_table",
    "render_tier_table",
    "render_queue_table",
    "render_alerts_table",
    "render_request_table",
    "render_cap_history_table",
    # Cards
    "render_metric_card",
    "render_status_card",
    "render_tier_card",
    "render_alert_card",
    "render_kpi_row",
    "render_utilization_bar",
]
