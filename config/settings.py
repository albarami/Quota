"""
Application settings and configuration management.

This module provides:
- Environment variable loading via pydantic-settings
- Parameter registry defaults for the quota system
- Database connection settings
- Azure OpenAI configuration

Usage:
    from config.settings import get_settings
    settings = get_settings()
    print(settings.DATABASE_URL)
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        APP_NAME: Application display name.
        APP_VERSION: Current application version.
        DEBUG: Enable debug mode.
        DATABASE_URL: SQLAlchemy database connection string.
        AZURE_OPENAI_API_KEY: Azure OpenAI API key.
        AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL.
        AZURE_OPENAI_API_VERSION: Azure OpenAI API version.
        AZURE_OPENAI_DEPLOYMENT: Azure OpenAI deployment/model name.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # =========================================
    # Application Settings
    # =========================================
    APP_NAME: str = "Qatar Nationality Quota System"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # =========================================
    # Database Settings
    # =========================================
    DATABASE_URL: str = Field(
        default="sqlite:///./data/quota.db",
        description="SQLAlchemy database connection string"
    )
    
    # =========================================
    # Azure OpenAI Settings
    # =========================================
    AZURE_OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="Azure OpenAI API key"
    )
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(
        default=None,
        description="Azure OpenAI endpoint URL"
    )
    AZURE_OPENAI_API_VERSION: str = Field(
        default="2024-02-15-preview",
        description="Azure OpenAI API version"
    )
    AZURE_OPENAI_DEPLOYMENT: str = Field(
        default="gpt-4o",
        description="Azure OpenAI deployment/model name"
    )
    
    # =========================================
    # API Settings
    # =========================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # =========================================
    # Streamlit Settings
    # =========================================
    STREAMLIT_PORT: int = 8501


class ParameterRegistry:
    """
    Default parameter values for the quota system.
    
    These values can be overridden by entries in the parameter_registry table.
    All thresholds are based on the technical specification document.
    """
    
    # =========================================
    # Tier Classification Thresholds
    # =========================================
    TIER_1_THRESHOLD: float = 0.15  # >15% of requests = Primary
    TIER_2_THRESHOLD: float = 0.05  # 5-15% of requests = Secondary
    TIER_3_THRESHOLD: float = 0.01  # 1-5% of requests = Minor
    # <1% = Tier 4 (Unusual)
    
    TIER_HYSTERESIS: float = 0.02  # ±2% to prevent tier oscillation
    MIN_REQUESTS_FOR_TIER: int = 50  # Minimum sample for tier assignment
    
    # =========================================
    # Dominance Alert Thresholds
    # =========================================
    DOMINANCE_CRITICAL: float = 0.50  # >50% share = Block new approvals
    DOMINANCE_HIGH: float = 0.40  # 40-50% share = Partial approve only
    DOMINANCE_WATCH: float = 0.30  # 30-40% share = Flag for review
    
    VELOCITY_CRITICAL: float = 0.10  # >10pp/3yr = Accelerating dominance
    MIN_PROFESSION_SIZE: int = 200  # Dominance rules only apply above this
    
    # =========================================
    # Capacity & Queue Parameters
    # =========================================
    PROJECTION_HORIZON_DAYS: int = 180  # Rolling forecast window (6 months)
    OUTFLOW_CONFIDENCE_FACTOR: float = 0.75  # Conservative buffer
    PENDING_APPROVAL_RATE: float = 0.80  # Assumed approval rate for pending
    
    QUEUE_EXPIRY_DAYS: int = 90  # Request expires if not processed
    QUEUE_CONFIRM_DAYS: int = 30  # Applicant must confirm continued interest
    MAX_QUEUE_PER_TIER: int = 200  # Max queued requests per nationality-tier
    
    RECALC_FREQUENCY_MINS: int = 15  # Tier status recalculation interval
    
    # =========================================
    # Utilization Thresholds
    # =========================================
    UTILIZATION_HIGH: float = 0.90  # >90% = high utilization (+20 priority)
    UTILIZATION_MEDIUM: float = 0.70  # 70-90% = medium (+10 priority)
    UTILIZATION_LOW: float = 0.30  # <30% = low (-20 priority)
    
    # =========================================
    # Priority Score Points
    # =========================================
    PRIORITY_HIGH_DEMAND_SKILL: int = 50
    PRIORITY_STRATEGIC_SECTOR: int = 30
    PRIORITY_HIGH_UTILIZATION: int = 20
    PRIORITY_MEDIUM_UTILIZATION: int = 10
    PRIORITY_LOW_UTILIZATION: int = -20
    PRIORITY_SMALL_ESTABLISHMENT: int = 10
    SMALL_ESTABLISHMENT_THRESHOLD: int = 50  # <50 workers
    
    # =========================================
    # Forecast & Monitoring
    # =========================================
    FORECAST_ACCURACY_THRESHOLD: float = 0.15  # ±15% acceptable
    FORECAST_ALERT_THRESHOLD: float = 0.20  # >20% triggers alert
    EMERGENCY_HEADROOM_THRESHOLD: int = 50  # <50 = emergency mode
    
    # =========================================
    # Data Freshness (minutes)
    # =========================================
    DATA_FRESHNESS_LIVE: int = 15  # Real-time data threshold
    DATA_FRESHNESS_DELAYED: int = 60  # Delayed data threshold
    DATA_FRESHNESS_STALE: int = 240  # Stale data threshold (4 hours)
    
    @classmethod
    def get_all_parameters(cls) -> dict:
        """
        Get all parameter values as a dictionary.
        
        Returns:
            dict: All parameter names and their default values.
        """
        return {
            key: value for key, value in vars(cls).items()
            if not key.startswith("_") and not callable(value)
        }


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings instance.
    
    Returns:
        Settings: Application settings loaded from environment.
    """
    return Settings()


def get_parameter(name: str, default: any = None) -> any:
    """
    Get a parameter value from the registry.
    
    Args:
        name: Parameter name (e.g., 'TIER_1_THRESHOLD').
        default: Default value if parameter not found.
        
    Returns:
        Parameter value or default.
    """
    return getattr(ParameterRegistry, name, default)


# Strategic sectors that receive priority scoring bonus
STRATEGIC_SECTORS = [
    "Healthcare",
    "Information Technology",
    "Education",
    "Financial Services",
    "Energy",
]

# Restricted nationalities (from technical specification)
RESTRICTED_NATIONALITIES = [
    {"code": "EGY", "name": "Egypt"},
    {"code": "IND", "name": "India"},
    {"code": "PAK", "name": "Pakistan"},
    {"code": "NPL", "name": "Nepal"},
    {"code": "BGD", "name": "Bangladesh"},
    {"code": "PHL", "name": "Philippines"},
    {"code": "IRN", "name": "Iran"},
    {"code": "IRQ", "name": "Iraq"},
    {"code": "YEM", "name": "Yemen"},
    {"code": "SYR", "name": "Syria"},
    {"code": "AFG", "name": "Afghanistan"},
]
