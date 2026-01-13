"""
Pytest configuration and fixtures.

Provides test database, sample data, and common fixtures.
"""

import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.base import Base
from src.models import (
    Nationality,
    Profession,
    EconomicActivity,
    Establishment,
    NationalityCap,
    NationalityTier,
    WorkerStock,
    WorkerState,
    QuotaRequest,
    RequestStatus,
    RequestQueue,
    DominanceAlert,
    AlertLevel,
    DecisionLog,
    DecisionType,
)


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """
    Create a test database session.
    
    Each test gets a fresh transaction that is rolled back after.
    """
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_nationalities(db_session: Session) -> list[Nationality]:
    """Create sample nationalities."""
    nationalities = [
        Nationality(code="EGY", name="Egypt", is_restricted=True),
        Nationality(code="BGD", name="Bangladesh", is_restricted=True),
        Nationality(code="IND", name="India", is_restricted=True),
        Nationality(code="NPL", name="Nepal", is_restricted=True),
        Nationality(code="USA", name="United States", is_restricted=False),
    ]
    db_session.add_all(nationalities)
    db_session.commit()
    return nationalities


@pytest.fixture
def sample_professions(db_session: Session) -> list[Profession]:
    """Create sample professions."""
    professions = [
        Profession(code="CONST_SUP", name="Construction Supervisor", high_demand_flag=True),
        Profession(code="SITE_ENG", name="Site Engineer", high_demand_flag=True),
        Profession(code="GEN_LAB", name="General Labourer", high_demand_flag=False),
        Profession(code="ELEC", name="Electrician", high_demand_flag=True),
        Profession(code="PLUMB", name="Plumber", high_demand_flag=False),
    ]
    db_session.add_all(professions)
    db_session.commit()
    return professions


@pytest.fixture
def sample_activities(db_session: Session) -> list[EconomicActivity]:
    """Create sample economic activities."""
    activities = [
        EconomicActivity(code="CONST", name="Construction", is_strategic=True),
        EconomicActivity(code="MAINT", name="Maintenance", is_strategic=False),
        EconomicActivity(code="MANUF", name="Manufacturing", is_strategic=True),
    ]
    db_session.add_all(activities)
    db_session.commit()
    return activities


@pytest.fixture
def sample_establishments(db_session: Session, sample_activities: list) -> list[Establishment]:
    """Create sample establishments."""
    establishments = [
        Establishment(
            name="Test Construction LLC",
            qid="QID001",
            activity_id=sample_activities[0].id,
            workforce_size=500,
            utilization_rate=0.85,
            is_small=False,
        ),
        Establishment(
            name="Small Services Co",
            qid="QID002",
            activity_id=sample_activities[1].id,
            workforce_size=20,
            utilization_rate=0.60,
            is_small=True,
        ),
    ]
    db_session.add_all(establishments)
    db_session.commit()
    return establishments


@pytest.fixture
def sample_caps(db_session: Session, sample_nationalities: list) -> list[NationalityCap]:
    """Create sample nationality caps."""
    current_year = date.today().year
    caps = [
        NationalityCap(
            nationality_id=sample_nationalities[0].id,  # Egypt
            year=current_year,
            cap_limit=15000,
            previous_cap=14000,
            set_by="Test",
            set_date=date.today(),
        ),
        NationalityCap(
            nationality_id=sample_nationalities[1].id,  # Bangladesh
            year=current_year,
            cap_limit=20000,
            previous_cap=18000,
            set_by="Test",
            set_date=date.today(),
        ),
    ]
    db_session.add_all(caps)
    db_session.commit()
    return caps


@pytest.fixture
def sample_tiers(
    db_session: Session,
    sample_nationalities: list,
    sample_professions: list
) -> list[NationalityTier]:
    """Create sample tier classifications."""
    tiers = [
        # Egypt - Construction Supervisor is Tier 1
        NationalityTier(
            nationality_id=sample_nationalities[0].id,
            profession_id=sample_professions[0].id,
            tier_level=1,
            share_pct=0.33,
            request_count=5000,
            valid_from=date.today(),
        ),
        # Egypt - Site Engineer is Tier 2
        NationalityTier(
            nationality_id=sample_nationalities[0].id,
            profession_id=sample_professions[1].id,
            tier_level=2,
            share_pct=0.12,
            request_count=1800,
            valid_from=date.today(),
        ),
        # Egypt - General Labourer is Tier 3
        NationalityTier(
            nationality_id=sample_nationalities[0].id,
            profession_id=sample_professions[2].id,
            tier_level=3,
            share_pct=0.03,
            request_count=450,
            valid_from=date.today(),
        ),
    ]
    db_session.add_all(tiers)
    db_session.commit()
    return tiers


@pytest.fixture
def sample_workers(
    db_session: Session,
    sample_nationalities: list,
    sample_professions: list,
    sample_establishments: list,
) -> list[WorkerStock]:
    """Create sample worker records."""
    workers = []
    
    # Create 100 Egyptian workers in construction
    for i in range(100):
        worker = WorkerStock(
            qid=f"W{i:06d}",
            nationality_id=sample_nationalities[0].id,  # Egypt
            profession_id=sample_professions[0].id,  # Construction Supervisor
            establishment_id=sample_establishments[0].id,
            state=WorkerState.IN_COUNTRY,
            employment_start=date.today() - timedelta(days=365),
            employment_end=date.today() + timedelta(days=365),
            visa_expiry_date=date.today() + timedelta(days=365),
        )
        workers.append(worker)
    
    # Create 50 Egyptian workers as Site Engineers
    for i in range(100, 150):
        worker = WorkerStock(
            qid=f"W{i:06d}",
            nationality_id=sample_nationalities[0].id,
            profession_id=sample_professions[1].id,
            establishment_id=sample_establishments[0].id,
            state=WorkerState.IN_COUNTRY,
            employment_start=date.today() - timedelta(days=365),
        )
        workers.append(worker)
    
    db_session.add_all(workers)
    db_session.commit()
    return workers


@pytest.fixture
def sample_request(
    db_session: Session,
    sample_nationalities: list,
    sample_professions: list,
    sample_establishments: list,
) -> QuotaRequest:
    """Create a sample quota request."""
    request = QuotaRequest(
        establishment_id=sample_establishments[0].id,
        nationality_id=sample_nationalities[0].id,
        profession_id=sample_professions[0].id,
        requested_count=10,
        status=RequestStatus.SUBMITTED,
        submitted_date=datetime.utcnow(),
    )
    db_session.add(request)
    db_session.commit()
    return request


# Helper functions for tests
def create_workers_for_dominance(
    db_session: Session,
    nationality_id: int,
    profession_id: int,
    establishment_id: int,
    count: int,
    state: WorkerState = WorkerState.IN_COUNTRY
) -> list[WorkerStock]:
    """Helper to create workers for dominance testing."""
    workers = []
    for i in range(count):
        worker = WorkerStock(
            qid=f"DOM{nationality_id}{profession_id}{i:04d}",
            nationality_id=nationality_id,
            profession_id=profession_id,
            establishment_id=establishment_id,
            state=state,
            employment_start=date.today() - timedelta(days=180),
        )
        workers.append(worker)
    db_session.add_all(workers)
    db_session.commit()
    return workers
