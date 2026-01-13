#!/usr/bin/env python
"""
Database initialization script.

This script:
1. Creates all database tables
2. Initializes default parameters from the registry
3. Creates sample restricted nationalities

Run this script once during initial setup:
    python scripts/init_db.py

Usage:
    python scripts/init_db.py          # Initialize database
    python scripts/init_db.py --reset  # Drop and recreate all tables
"""

import argparse
import os
import sys
from datetime import date

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    Base,
    engine,
    SessionLocal,
    Nationality,
    ParameterRegistry,
    DEFAULT_PARAMETERS,
)


def create_tables() -> None:
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("[OK] Tables created successfully")


def drop_tables() -> None:
    """Drop all database tables."""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("[OK] Tables dropped")


def init_parameters(db) -> None:
    """Initialize default parameters from registry."""
    print("Initializing default parameters...")
    
    for param_def in DEFAULT_PARAMETERS:
        # Check if parameter already exists
        existing = db.query(ParameterRegistry).filter(
            ParameterRegistry.parameter_name == param_def["parameter_name"],
            ParameterRegistry.valid_to.is_(None)
        ).first()
        
        if existing:
            print(f"  - {param_def['parameter_name']}: already exists, skipping")
            continue
        
        param = ParameterRegistry(
            parameter_name=param_def["parameter_name"],
            value=param_def["value"],
            value_type=param_def["value_type"],
            category=param_def["category"],
            description=param_def["description"],
            min_value=param_def.get("min_value"),
            max_value=param_def.get("max_value"),
            valid_from=date.today(),
            changed_by="system_init",
            change_reason="Initial system setup",
        )
        db.add(param)
        print(f"  + {param_def['parameter_name']}: {param_def['value']}")
    
    db.commit()
    print(f"[OK] {len(DEFAULT_PARAMETERS)} parameters initialized")


def init_nationalities(db) -> None:
    """Initialize restricted nationalities."""
    print("Initializing restricted nationalities...")
    
    nationalities = [
        # Restricted nationalities (from technical specification)
        {"code": "EGY", "name": "Egypt", "is_restricted": True, "continent": "Africa"},
        {"code": "IND", "name": "India", "is_restricted": True, "continent": "Asia"},
        {"code": "PAK", "name": "Pakistan", "is_restricted": True, "continent": "Asia"},
        {"code": "NPL", "name": "Nepal", "is_restricted": True, "continent": "Asia"},
        {"code": "BGD", "name": "Bangladesh", "is_restricted": True, "continent": "Asia"},
        {"code": "PHL", "name": "Philippines", "is_restricted": True, "continent": "Asia"},
        {"code": "IRN", "name": "Iran", "is_restricted": True, "continent": "Asia"},
        {"code": "IRQ", "name": "Iraq", "is_restricted": True, "continent": "Asia"},
        {"code": "YEM", "name": "Yemen", "is_restricted": True, "continent": "Asia"},
        {"code": "SYR", "name": "Syria", "is_restricted": True, "continent": "Asia"},
        {"code": "AFG", "name": "Afghanistan", "is_restricted": True, "continent": "Asia"},
        # GCC countries (not restricted)
        {"code": "SAU", "name": "Saudi Arabia", "is_restricted": False, "is_gcc": True, "continent": "Asia"},
        {"code": "UAE", "name": "United Arab Emirates", "is_restricted": False, "is_gcc": True, "continent": "Asia"},
        {"code": "KWT", "name": "Kuwait", "is_restricted": False, "is_gcc": True, "continent": "Asia"},
        {"code": "BHR", "name": "Bahrain", "is_restricted": False, "is_gcc": True, "continent": "Asia"},
        {"code": "OMN", "name": "Oman", "is_restricted": False, "is_gcc": True, "continent": "Asia"},
        # Other common nationalities (not restricted)
        {"code": "LKA", "name": "Sri Lanka", "is_restricted": False, "continent": "Asia"},
        {"code": "IDN", "name": "Indonesia", "is_restricted": False, "continent": "Asia"},
        {"code": "JOR", "name": "Jordan", "is_restricted": False, "continent": "Asia"},
        {"code": "LBN", "name": "Lebanon", "is_restricted": False, "continent": "Asia"},
    ]
    
    for nat_data in nationalities:
        # Check if nationality already exists
        existing = db.query(Nationality).filter(
            Nationality.code == nat_data["code"]
        ).first()
        
        if existing:
            print(f"  - {nat_data['code']}: already exists, skipping")
            continue
        
        nationality = Nationality(
            code=nat_data["code"],
            name=nat_data["name"],
            is_restricted=nat_data.get("is_restricted", False),
            is_gcc=nat_data.get("is_gcc", False),
            continent=nat_data.get("continent"),
        )
        db.add(nationality)
        restricted_marker = " [RESTRICTED]" if nat_data.get("is_restricted") else ""
        print(f"  + {nat_data['code']}: {nat_data['name']}{restricted_marker}")
    
    db.commit()
    print(f"[OK] {len(nationalities)} nationalities initialized")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Initialize the quota database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables before creating (WARNING: destroys data)"
    )
    args = parser.parse_args()
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    print("=" * 50)
    print("Nationality Quota System - Database Initialization")
    print("=" * 50)
    print()
    
    if args.reset:
        print("WARNING: This will delete all existing data!")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return
        drop_tables()
        print()
    
    create_tables()
    print()
    
    # Initialize data
    db = SessionLocal()
    try:
        init_parameters(db)
        print()
        init_nationalities(db)
        print()
        print("=" * 50)
        print("[OK] Database initialization complete!")
        print("=" * 50)
        print()
        print("Next steps:")
        print("  1. Run: python scripts/generate_synthetic_data.py")
        print("  2. Start API: uvicorn src.api.main:app --reload")
        print("  3. Start UI: streamlit run app/streamlit_app.py")
    finally:
        db.close()


if __name__ == "__main__":
    main()
