"""
Configuration and parameter registry models.

This module defines:
- ParameterRegistry: Database-stored configurable parameters

Parameters are version-controlled and changes require Policy Committee approval.
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import Column, Date, DateTime, Float, Integer, String, Text

from src.models.base import BaseModel


class ParameterRegistry(BaseModel):
    """
    Parameter registry for configurable thresholds.
    
    All configurable thresholds are maintained in this table.
    Parameters are version-controlled and audited.
    
    Attributes:
        parameter_name: Unique parameter identifier.
        value: Parameter value (stored as string, converted as needed).
        value_type: Type of value (int, float, string, bool).
        category: Parameter category for grouping.
        description: Human-readable description.
        min_value: Minimum allowed value (for validation).
        max_value: Maximum allowed value (for validation).
        valid_from: Start of validity period.
        valid_to: End of validity period (null if current).
        changed_by: Who changed this parameter.
        change_reason: Why the change was made.
    """
    
    __tablename__ = "parameter_registry"
    
    parameter_name = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Unique parameter identifier"
    )
    value = Column(
        String(200),
        nullable=False,
        doc="Parameter value (stored as string)"
    )
    value_type = Column(
        String(20),
        default="float",
        nullable=False,
        doc="Type of value (int, float, string, bool)"
    )
    category = Column(
        String(50),
        nullable=True,
        index=True,
        doc="Parameter category for grouping"
    )
    description = Column(
        Text,
        nullable=True,
        doc="Human-readable description"
    )
    min_value = Column(
        Float,
        nullable=True,
        doc="Minimum allowed value"
    )
    max_value = Column(
        Float,
        nullable=True,
        doc="Maximum allowed value"
    )
    valid_from = Column(
        Date,
        default=date.today,
        nullable=False,
        doc="Start of validity period"
    )
    valid_to = Column(
        Date,
        nullable=True,
        doc="End of validity period (null if current)"
    )
    changed_by = Column(
        String(100),
        nullable=True,
        doc="Who changed this parameter"
    )
    change_reason = Column(
        Text,
        nullable=True,
        doc="Why the change was made"
    )
    
    @property
    def is_current(self) -> bool:
        """Check if this parameter version is currently valid."""
        today = date.today()
        if self.valid_to is None:
            return self.valid_from <= today
        return self.valid_from <= today <= self.valid_to
    
    def get_typed_value(self) -> Any:
        """
        Get parameter value converted to its proper type.
        
        Returns:
            Value converted to int, float, bool, or string.
        """
        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ("true", "1", "yes")
        else:
            return self.value
    
    def validate_value(self, new_value: Any) -> tuple[bool, str]:
        """
        Validate a new value against constraints.
        
        Args:
            new_value: Value to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            # Convert to numeric for range validation
            if self.value_type in ("int", "float"):
                numeric_value = float(new_value)
                
                if self.min_value is not None and numeric_value < self.min_value:
                    return False, f"Value {new_value} below minimum {self.min_value}"
                
                if self.max_value is not None and numeric_value > self.max_value:
                    return False, f"Value {new_value} above maximum {self.max_value}"
            
            return True, ""
            
        except (ValueError, TypeError) as e:
            return False, f"Invalid value type: {str(e)}"
    
    def __repr__(self) -> str:
        return f"<ParameterRegistry(name='{self.parameter_name}', value='{self.value}')>"


# Default parameter definitions for initialization
DEFAULT_PARAMETERS = [
    # Tier Classification
    {
        "parameter_name": "TIER_1_THRESHOLD",
        "value": "0.15",
        "value_type": "float",
        "category": "tier_classification",
        "description": "Threshold for Tier 1 (Primary): >15% of requests",
        "min_value": 0.10,
        "max_value": 0.25,
    },
    {
        "parameter_name": "TIER_2_THRESHOLD",
        "value": "0.05",
        "value_type": "float",
        "category": "tier_classification",
        "description": "Threshold for Tier 2 (Secondary): 5-15% of requests",
        "min_value": 0.03,
        "max_value": 0.10,
    },
    {
        "parameter_name": "TIER_3_THRESHOLD",
        "value": "0.01",
        "value_type": "float",
        "category": "tier_classification",
        "description": "Threshold for Tier 3 (Minor): 1-5% of requests",
        "min_value": 0.005,
        "max_value": 0.03,
    },
    {
        "parameter_name": "TIER_HYSTERESIS",
        "value": "0.02",
        "value_type": "float",
        "category": "tier_classification",
        "description": "Hysteresis band to prevent tier oscillation (±2%)",
        "min_value": 0.01,
        "max_value": 0.05,
    },
    {
        "parameter_name": "MIN_REQUESTS_FOR_TIER",
        "value": "50",
        "value_type": "int",
        "category": "tier_classification",
        "description": "Minimum requests needed for tier assignment",
        "min_value": 20,
        "max_value": 100,
    },
    # Dominance Alerts
    {
        "parameter_name": "DOMINANCE_CRITICAL",
        "value": "0.50",
        "value_type": "float",
        "category": "dominance_alert",
        "description": "Critical dominance threshold: >50% share blocks approvals",
        "min_value": 0.45,
        "max_value": 0.60,
    },
    {
        "parameter_name": "DOMINANCE_HIGH",
        "value": "0.40",
        "value_type": "float",
        "category": "dominance_alert",
        "description": "High dominance threshold: 40-50% share, partial only",
        "min_value": 0.35,
        "max_value": 0.50,
    },
    {
        "parameter_name": "DOMINANCE_WATCH",
        "value": "0.30",
        "value_type": "float",
        "category": "dominance_alert",
        "description": "Watch dominance threshold: 30-40% share, flag for review",
        "min_value": 0.25,
        "max_value": 0.40,
    },
    {
        "parameter_name": "VELOCITY_CRITICAL",
        "value": "0.10",
        "value_type": "float",
        "category": "dominance_alert",
        "description": "Critical velocity: >10pp per 3 years",
        "min_value": 0.08,
        "max_value": 0.15,
    },
    {
        "parameter_name": "MIN_PROFESSION_SIZE",
        "value": "200",
        "value_type": "int",
        "category": "dominance_alert",
        "description": "Minimum profession size for dominance rules",
        "min_value": 100,
        "max_value": 500,
    },
    # Capacity & Queue
    {
        "parameter_name": "PROJECTION_HORIZON_DAYS",
        "value": "30",
        "value_type": "int",
        "category": "capacity",
        "description": "Rolling forecast window in days",
        "min_value": 14,
        "max_value": 60,
    },
    {
        "parameter_name": "OUTFLOW_CONFIDENCE_FACTOR",
        "value": "0.75",
        "value_type": "float",
        "category": "capacity",
        "description": "Conservative buffer on outflow projections",
        "min_value": 0.60,
        "max_value": 0.90,
    },
    {
        "parameter_name": "PENDING_APPROVAL_RATE",
        "value": "0.80",
        "value_type": "float",
        "category": "capacity",
        "description": "Assumed approval rate for pending requests",
        "min_value": 0.70,
        "max_value": 0.90,
    },
    {
        "parameter_name": "QUEUE_EXPIRY_DAYS",
        "value": "90",
        "value_type": "int",
        "category": "queue",
        "description": "Days until queue entry expires",
        "min_value": 60,
        "max_value": 120,
    },
    {
        "parameter_name": "QUEUE_CONFIRM_DAYS",
        "value": "30",
        "value_type": "int",
        "category": "queue",
        "description": "Days until confirmation required",
        "min_value": 20,
        "max_value": 45,
    },
    {
        "parameter_name": "MAX_QUEUE_PER_TIER",
        "value": "200",
        "value_type": "int",
        "category": "queue",
        "description": "Maximum queued requests per nationality-tier",
        "min_value": 100,
        "max_value": 500,
    },
    {
        "parameter_name": "RECALC_FREQUENCY_MINS",
        "value": "15",
        "value_type": "int",
        "category": "system",
        "description": "Tier status recalculation interval (minutes)",
        "min_value": 5,
        "max_value": 60,
    },
]
