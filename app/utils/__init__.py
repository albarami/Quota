"""
Utility modules for Streamlit app.
"""

from app.utils.db_queries import (
    get_dashboard_data,
    get_all_nationalities,
    get_cap_data,
)

__all__ = [
    "get_dashboard_data",
    "get_all_nationalities",
    "get_cap_data",
]
