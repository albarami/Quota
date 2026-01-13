"""
SQLAlchemy base configuration and database engine setup.

This module provides:
- Base class for all SQLAlchemy models
- Database engine and session management
- Common mixins for timestamps and soft delete

Usage:
    from src.models.base import Base, get_db, engine
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    with get_db() as db:
        db.query(Model).all()
"""

import os
from datetime import datetime
from typing import Generator

from sqlalchemy import Column, DateTime, Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/quota.db")

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Provides common configuration and can be extended with mixins.
    """
    pass


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamps.
    
    Attributes:
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Timestamp when record was created"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Timestamp when record was last updated"
    )


class BaseModel(Base, TimestampMixin):
    """
    Abstract base model with ID and timestamps.
    
    All models should inherit from this class to get:
    - Auto-incrementing integer primary key
    - created_at and updated_at timestamps
    
    Attributes:
        id: Primary key.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """
    
    __abstract__ = True
    
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        doc="Primary key"
    )


def get_db() -> Generator[Session, None, None]:
    """
    Get database session as context manager.
    
    Yields:
        Session: SQLAlchemy database session.
        
    Example:
        with get_db() as db:
            users = db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    """
    Initialize database by creating all tables.
    
    This function creates all tables defined in models that inherit from Base.
    Should be called once during application startup or setup.
    """
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Import all models to register them with Base
    from src.models import config, core, quota, request, worker  # noqa: F401
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


def drop_database() -> None:
    """
    Drop all tables from the database.
    
    WARNING: This will delete all data! Use with caution.
    """
    Base.metadata.drop_all(bind=engine)
