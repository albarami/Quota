"""
Configuration module for Nationality Quota Allocation System.

This module provides centralized configuration management including:
- Environment variable loading
- Parameter registry defaults
- Database settings
- Azure OpenAI configuration
"""

from config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
