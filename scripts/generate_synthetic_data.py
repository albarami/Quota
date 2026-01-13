#!/usr/bin/env python
"""
Synthetic data generation script for Qatar labor market simulation.

Generates realistic data based on the technical specification:
- 11 restricted nationalities with unique demand patterns
- 50+ professions across sectors
- 500+ establishments with varying utilization
- 150,000+ worker records
- Historical request data
- Dominance scenarios

Run after init_db.py:
    python scripts/generate_synthetic_data.py
"""

import os
import random
import sys
from datetime import date, datetime, timedelta
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    SessionLocal,
    Nationality,
    Profession,
    EconomicActivity,
    Establishment,
    NationalityCap,
    NationalityTier,
    DominanceAlert,
    WorkerStock,
    WorkerState,
    QuotaRequest,
    RequestQueue,
    RequestStatus,
    AlertLevel,
)

# Set random seed for reproducibility
random.seed(42)


# ============================================
# PROFESSION DEFINITIONS
# ============================================
PROFESSIONS = [
    # Construction (high demand)
    {"code": "CONST_SUP", "name": "Construction Supervisor", "category": "Construction", "high_demand": True},
    {"code": "CONST_ENG", "name": "Construction Engineer", "category": "Construction", "high_demand": True},
    {"code": "CONST_LAB", "name": "Construction Labourer", "category": "Construction", "high_demand": False},
    {"code": "WELDER", "name": "Welder", "category": "Construction", "high_demand": True},
    {"code": "ELEC", "name": "Electrician", "category": "Construction", "high_demand": True},
    {"code": "PLUMBER", "name": "Plumber", "category": "Construction", "high_demand": False},
    {"code": "CARPENTER", "name": "Carpenter", "category": "Construction", "high_demand": False},
    {"code": "MASON", "name": "Mason", "category": "Construction", "high_demand": False},
    {"code": "PAINTER", "name": "Painter", "category": "Construction", "high_demand": False},
    {"code": "HVAC_TECH", "name": "HVAC Technician", "category": "Construction", "high_demand": True},
    # Engineering
    {"code": "CIVIL_ENG", "name": "Civil Engineer", "category": "Engineering", "high_demand": True},
    {"code": "MECH_ENG", "name": "Mechanical Engineer", "category": "Engineering", "high_demand": True},
    {"code": "ELEC_ENG", "name": "Electrical Engineer", "category": "Engineering", "high_demand": True},
    {"code": "CHEM_ENG", "name": "Chemical Engineer", "category": "Engineering", "high_demand": True},
    {"code": "PROJ_MGR", "name": "Project Manager", "category": "Engineering", "high_demand": True},
    # IT (strategic sector)
    {"code": "SW_DEV", "name": "Software Developer", "category": "IT", "high_demand": True},
    {"code": "NET_ENG", "name": "Network Engineer", "category": "IT", "high_demand": True},
    {"code": "DATA_ANALYST", "name": "Data Analyst", "category": "IT", "high_demand": True},
    {"code": "IT_SUPPORT", "name": "IT Support Specialist", "category": "IT", "high_demand": False},
    {"code": "CYBER_SEC", "name": "Cybersecurity Specialist", "category": "IT", "high_demand": True},
    # Healthcare (strategic sector)
    {"code": "DOCTOR", "name": "Medical Doctor", "category": "Healthcare", "high_demand": True},
    {"code": "NURSE", "name": "Nurse", "category": "Healthcare", "high_demand": True},
    {"code": "PHARMACIST", "name": "Pharmacist", "category": "Healthcare", "high_demand": True},
    {"code": "LAB_TECH", "name": "Laboratory Technician", "category": "Healthcare", "high_demand": False},
    {"code": "RADIOLOGIST", "name": "Radiologist", "category": "Healthcare", "high_demand": True},
    # Transport
    {"code": "TRUCK_DRV", "name": "Heavy Truck Driver", "category": "Transport", "high_demand": True},
    {"code": "BUS_DRV", "name": "Bus Driver", "category": "Transport", "high_demand": False},
    {"code": "LOGISTICS", "name": "Logistics Coordinator", "category": "Transport", "high_demand": False},
    {"code": "FORKLIFT", "name": "Forklift Operator", "category": "Transport", "high_demand": False},
    # Hospitality
    {"code": "HOTEL_MGR", "name": "Hotel Manager", "category": "Hospitality", "high_demand": False},
    {"code": "CHEF", "name": "Chef", "category": "Hospitality", "high_demand": False},
    {"code": "WAITER", "name": "Waiter", "category": "Hospitality", "high_demand": False},
    {"code": "HOUSEKEEP", "name": "Housekeeper", "category": "Hospitality", "high_demand": False},
    {"code": "RECEPTIONIST", "name": "Receptionist", "category": "Hospitality", "high_demand": False},
    # Security
    {"code": "SEC_GUARD", "name": "Security Guard", "category": "Security", "high_demand": False},
    {"code": "SEC_SUP", "name": "Security Supervisor", "category": "Security", "high_demand": False},
    # Finance
    {"code": "ACCOUNTANT", "name": "Accountant", "category": "Finance", "high_demand": False},
    {"code": "FIN_ANALYST", "name": "Financial Analyst", "category": "Finance", "high_demand": True},
    {"code": "AUDITOR", "name": "Auditor", "category": "Finance", "high_demand": False},
    # Education (strategic sector)
    {"code": "TEACHER", "name": "Teacher", "category": "Education", "high_demand": True},
    {"code": "PROFESSOR", "name": "Professor", "category": "Education", "high_demand": True},
    {"code": "TRAINER", "name": "Corporate Trainer", "category": "Education", "high_demand": False},
    # Retail
    {"code": "SALES_MGR", "name": "Sales Manager", "category": "Retail", "high_demand": False},
    {"code": "CASHIER", "name": "Cashier", "category": "Retail", "high_demand": False},
    {"code": "STORE_SUP", "name": "Store Supervisor", "category": "Retail", "high_demand": False},
    # Manufacturing
    {"code": "FACTORY_WKR", "name": "Factory Worker", "category": "Manufacturing", "high_demand": False},
    {"code": "QUALITY_CTL", "name": "Quality Controller", "category": "Manufacturing", "high_demand": False},
    {"code": "MACHINE_OP", "name": "Machine Operator", "category": "Manufacturing", "high_demand": False},
    # Oil & Gas
    {"code": "PETRO_ENG", "name": "Petroleum Engineer", "category": "Oil & Gas", "high_demand": True},
    {"code": "RIG_WORKER", "name": "Rig Worker", "category": "Oil & Gas", "high_demand": False},
    {"code": "PIPELINE_TECH", "name": "Pipeline Technician", "category": "Oil & Gas", "high_demand": True},
]

# ============================================
# ECONOMIC ACTIVITIES
# ============================================
ACTIVITIES = [
    {"code": "CONST", "name": "Construction", "sector": "Construction", "strategic": False},
    {"code": "OIL_GAS", "name": "Oil & Gas", "sector": "Energy", "strategic": True},
    {"code": "HEALTHCARE", "name": "Healthcare Services", "sector": "Healthcare", "strategic": True},
    {"code": "IT_SERVICES", "name": "IT Services", "sector": "IT", "strategic": True},
    {"code": "EDUCATION", "name": "Education", "sector": "Education", "strategic": True},
    {"code": "HOSPITALITY", "name": "Hospitality & Tourism", "sector": "Hospitality", "strategic": False},
    {"code": "RETAIL", "name": "Retail Trade", "sector": "Retail", "strategic": False},
    {"code": "FINANCE", "name": "Financial Services", "sector": "Finance", "strategic": True},
    {"code": "TRANSPORT", "name": "Transportation & Logistics", "sector": "Transport", "strategic": False},
    {"code": "MANUFACTURING", "name": "Manufacturing", "sector": "Manufacturing", "strategic": False},
    {"code": "SECURITY", "name": "Security Services", "sector": "Security", "strategic": False},
    {"code": "REAL_ESTATE", "name": "Real Estate", "sector": "Real Estate", "strategic": False},
]

# ============================================
# NATIONALITY DEMAND PATTERNS (from spec)
# ============================================
NATIONALITY_PATTERNS = {
    "EGY": {
        "stock": 8500, "cap": 10000,
        "tiers": {
            "CONST_SUP": 0.33, "CIVIL_ENG": 0.15, "MECH_ENG": 0.10,
            "TRUCK_DRV": 0.16, "WELDER": 0.10, "ELEC": 0.08
        },
        "dominance": {"CONST_SUP": 0.52, "CIVIL_ENG": 0.48}
    },
    "IND": {
        "stock": 45000, "cap": 50000,
        "tiers": {
            "SW_DEV": 0.20, "NET_ENG": 0.12, "DATA_ANALYST": 0.08,
            "CONST_LAB": 0.15, "ACCOUNTANT": 0.10, "SALES_MGR": 0.08
        },
        "dominance": {}
    },
    "PAK": {
        "stock": 25000, "cap": 28000,
        "tiers": {
            "CONST_LAB": 0.22, "SEC_GUARD": 0.18, "TRUCK_DRV": 0.15,
            "WELDER": 0.12, "ELEC": 0.08, "PLUMBER": 0.06
        },
        "dominance": {}
    },
    "NPL": {
        "stock": 35000, "cap": 38000,
        "tiers": {
            "SEC_GUARD": 0.25, "HOUSEKEEP": 0.18, "CONST_LAB": 0.15,
            "WAITER": 0.12, "FACTORY_WKR": 0.10
        },
        "dominance": {"SEC_GUARD": 0.35}
    },
    "BGD": {
        "stock": 28000, "cap": 32000,
        "tiers": {
            "CONST_LAB": 0.28, "FACTORY_WKR": 0.18, "MACHINE_OP": 0.12,
            "WELDER": 0.10, "PAINTER": 0.08
        },
        "dominance": {}
    },
    "PHL": {
        "stock": 22000, "cap": 25000,
        "tiers": {
            "NURSE": 0.25, "HOUSEKEEP": 0.15, "RECEPTIONIST": 0.12,
            "WAITER": 0.10, "CHEF": 0.08, "TEACHER": 0.06
        },
        "dominance": {"NURSE": 0.42}
    },
    "IRN": {
        "stock": 3200, "cap": 8000,
        "tiers": {
            "CIVIL_ENG": 0.35, "MECH_ENG": 0.23, "DOCTOR": 0.27,
            "PROFESSOR": 0.08
        },
        "dominance": {}
    },
    "IRQ": {
        "stock": 2800, "cap": 5000,
        "tiers": {
            "TRUCK_DRV": 0.42, "CONST_LAB": 0.28, "SEC_GUARD": 0.16,
            "WELDER": 0.09
        },
        "dominance": {}
    },
    "YEM": {
        "stock": 1500, "cap": 3000,
        "tiers": {
            "TRUCK_DRV": 0.35, "SEC_GUARD": 0.22, "CONST_LAB": 0.18,
            "SALES_MGR": 0.08
        },
        "dominance": {}
    },
    "SYR": {
        "stock": 2200, "cap": 5000,
        "tiers": {
            "CHEF": 0.18, "WAITER": 0.10, "HOTEL_MGR": 0.08,
            "SALES_MGR": 0.14, "CASHIER": 0.10, "TRUCK_DRV": 0.19
        },
        "dominance": {}
    },
    "AFG": {
        "stock": 1800, "cap": 2500,
        "tiers": {
            "SEC_GUARD": 0.48, "CONST_LAB": 0.32, "FACTORY_WKR": 0.10
        },
        "dominance": {}
    },
}


def create_professions(db) -> dict[str, int]:
    """Create profession records."""
    print("Creating professions...")
    profession_ids = {}
    
    for prof in PROFESSIONS:
        existing = db.query(Profession).filter(Profession.code == prof["code"]).first()
        if existing:
            profession_ids[prof["code"]] = existing.id
            continue
            
        p = Profession(
            code=prof["code"],
            name=prof["name"],
            category=prof["category"],
            high_demand_flag=prof.get("high_demand", False),
        )
        db.add(p)
        db.flush()
        profession_ids[prof["code"]] = p.id
    
    db.commit()
    print(f"  [OK] {len(PROFESSIONS)} professions created")
    return profession_ids


def create_activities(db) -> dict[str, int]:
    """Create economic activity records."""
    print("Creating economic activities...")
    activity_ids = {}
    
    for act in ACTIVITIES:
        existing = db.query(EconomicActivity).filter(EconomicActivity.code == act["code"]).first()
        if existing:
            activity_ids[act["code"]] = existing.id
            continue
            
        a = EconomicActivity(
            code=act["code"],
            name=act["name"],
            sector_group=act["sector"],
            is_strategic=act.get("strategic", False),
            strategic_weight=1.5 if act.get("strategic") else 1.0,
        )
        db.add(a)
        db.flush()
        activity_ids[act["code"]] = a.id
    
    db.commit()
    print(f"  [OK] {len(ACTIVITIES)} activities created")
    return activity_ids


def create_establishments(db, activity_ids: dict) -> list[int]:
    """Create establishment records."""
    print("Creating establishments...")
    establishment_ids = []
    
    # Check existing count
    existing_count = db.query(Establishment).count()
    if existing_count >= 500:
        print(f"  - {existing_count} establishments already exist, skipping")
        return [e.id for e in db.query(Establishment).all()]
    
    company_prefixes = [
        "Qatar", "Al", "Gulf", "National", "United", "Royal", "Premier",
        "Elite", "Golden", "Diamond", "Star", "Crown", "Phoenix", "Atlas"
    ]
    company_types = [
        "Construction", "Engineering", "Services", "Trading", "Industries",
        "Contracting", "Solutions", "Holdings", "Group", "International"
    ]
    
    activity_codes = list(activity_ids.keys())
    
    for i in range(550):
        prefix = random.choice(company_prefixes)
        ctype = random.choice(company_types)
        name = f"{prefix} {ctype} {'LLC' if random.random() > 0.3 else 'WLL'}"
        
        # Vary establishment sizes
        size_roll = random.random()
        if size_roll < 0.6:  # 60% small
            approved = random.randint(10, 49)
            size_cat = "Small"
        elif size_roll < 0.9:  # 30% medium
            approved = random.randint(50, 200)
            size_cat = "Medium"
        else:  # 10% large
            approved = random.randint(201, 1000)
            size_cat = "Large"
        
        # Utilization varies
        util_rate = random.uniform(0.3, 0.95)
        used = int(approved * util_rate)
        
        est = Establishment(
            name=f"{name} #{i+1}",
            license_number=f"CR{random.randint(100000, 999999)}",
            activity_id=activity_ids[random.choice(activity_codes)],
            total_approved=approved,
            total_used=used,
            size_category=size_cat,
            is_active=True,
        )
        db.add(est)
        db.flush()
        establishment_ids.append(est.id)
    
    db.commit()
    print(f"  [OK] {len(establishment_ids)} establishments created")
    return establishment_ids


def create_nationality_caps(db, nationality_ids: dict) -> None:
    """Create nationality cap records."""
    print("Creating nationality caps...")
    current_year = date.today().year
    
    for nat_code, nat_id in nationality_ids.items():
        if nat_code not in NATIONALITY_PATTERNS:
            continue
            
        pattern = NATIONALITY_PATTERNS[nat_code]
        
        # Check if cap exists
        existing = db.query(NationalityCap).filter(
            NationalityCap.nationality_id == nat_id,
            NationalityCap.year == current_year
        ).first()
        
        if existing:
            continue
        
        cap = NationalityCap(
            nationality_id=nat_id,
            year=current_year,
            cap_limit=pattern["cap"],
            previous_cap=int(pattern["cap"] * 0.9),  # 10% growth from last year
            set_by="Policy Committee",
            set_date=date(current_year, 1, 1),
            notes="Annual cap set based on demand analysis",
        )
        db.add(cap)
    
    db.commit()
    print(f"  [OK] Nationality caps created")


def create_nationality_tiers(db, nationality_ids: dict, profession_ids: dict) -> None:
    """Create tier classifications based on demand patterns."""
    print("Creating nationality tiers...")
    
    for nat_code, nat_id in nationality_ids.items():
        if nat_code not in NATIONALITY_PATTERNS:
            continue
            
        pattern = NATIONALITY_PATTERNS[nat_code]
        tiers = pattern.get("tiers", {})
        
        for prof_code, share in tiers.items():
            if prof_code not in profession_ids:
                continue
                
            # Check if tier exists
            existing = db.query(NationalityTier).filter(
                NationalityTier.nationality_id == nat_id,
                NationalityTier.profession_id == profession_ids[prof_code],
                NationalityTier.valid_to.is_(None)
            ).first()
            
            if existing:
                continue
            
            # Determine tier level
            if share >= 0.15:
                tier_level = 1
            elif share >= 0.05:
                tier_level = 2
            elif share >= 0.01:
                tier_level = 3
            else:
                tier_level = 4
            
            tier = NationalityTier(
                nationality_id=nat_id,
                profession_id=profession_ids[prof_code],
                tier_level=tier_level,
                share_pct=share,
                request_count=int(share * 1000),
                calculated_date=datetime.utcnow(),
                valid_from=date.today() - timedelta(days=30),
            )
            db.add(tier)
    
    db.commit()
    print(f"  [OK] Nationality tiers created")


def create_dominance_alerts(db, nationality_ids: dict, profession_ids: dict) -> None:
    """Create dominance alerts based on concentration scenarios."""
    print("Creating dominance alerts...")
    
    for nat_code, nat_id in nationality_ids.items():
        if nat_code not in NATIONALITY_PATTERNS:
            continue
            
        pattern = NATIONALITY_PATTERNS[nat_code]
        dominance = pattern.get("dominance", {})
        
        for prof_code, share in dominance.items():
            if prof_code not in profession_ids:
                continue
            
            # Check if alert exists
            existing = db.query(DominanceAlert).filter(
                DominanceAlert.nationality_id == nat_id,
                DominanceAlert.profession_id == profession_ids[prof_code],
                DominanceAlert.resolved_date.is_(None)
            ).first()
            
            if existing:
                continue
            
            # Determine alert level
            if share >= 0.50:
                level = AlertLevel.CRITICAL
            elif share >= 0.40:
                level = AlertLevel.HIGH
            elif share >= 0.30:
                level = AlertLevel.WATCH
            else:
                level = AlertLevel.OK
            
            # Calculate velocity (simulated)
            velocity = random.uniform(0.05, 0.15) if share > 0.40 else random.uniform(0.01, 0.05)
            
            alert = DominanceAlert(
                nationality_id=nat_id,
                profession_id=profession_ids[prof_code],
                share_pct=share,
                velocity=velocity,
                alert_level=level,
                total_in_profession=random.randint(5000, 15000),
                nationality_count=int(share * random.randint(5000, 15000)),
                threshold_breached=f"{level.value}_THRESHOLD",
                detected_date=datetime.utcnow() - timedelta(days=random.randint(30, 180)),
            )
            db.add(alert)
    
    db.commit()
    print(f"  [OK] Dominance alerts created")


def create_workers(
    db,
    nationality_ids: dict,
    profession_ids: dict,
    establishment_ids: list
) -> None:
    """Create worker records with realistic distribution."""
    print("Creating worker records (this may take a moment)...")
    
    # Check existing count
    existing_count = db.query(WorkerStock).count()
    if existing_count >= 100000:
        print(f"  - {existing_count} workers already exist, skipping")
        return
    
    worker_count = 0
    batch_size = 1000
    workers_batch = []
    
    for nat_code, nat_id in nationality_ids.items():
        if nat_code not in NATIONALITY_PATTERNS:
            continue
            
        pattern = NATIONALITY_PATTERNS[nat_code]
        target_stock = pattern["stock"]
        tiers = pattern.get("tiers", {})
        
        # Create workers distributed by profession
        for prof_code, share in tiers.items():
            if prof_code not in profession_ids:
                continue
                
            prof_worker_count = int(target_stock * share)
            
            for _ in range(prof_worker_count):
                # Random visa dates
                visa_issue = date.today() - timedelta(days=random.randint(30, 700))
                visa_expiry = visa_issue + timedelta(days=random.randint(365, 730))
                employment_start = visa_issue + timedelta(days=random.randint(1, 30))
                employment_end = visa_expiry - timedelta(days=random.randint(30, 90))
                
                # Determine state (95% in country, 3% committed, 2% pending)
                state_roll = random.random()
                if state_roll < 0.95:
                    state = WorkerState.IN_COUNTRY
                    entry_date = visa_issue + timedelta(days=random.randint(1, 14))
                elif state_roll < 0.98:
                    state = WorkerState.COMMITTED
                    entry_date = None
                else:
                    state = WorkerState.PENDING
                    entry_date = None
                
                worker = WorkerStock(
                    worker_id=f"W{nat_code}{worker_count:06d}",
                    nationality_id=nat_id,
                    profession_id=profession_ids[prof_code],
                    establishment_id=random.choice(establishment_ids),
                    state=state,
                    visa_number=f"V{random.randint(10000000, 99999999)}",
                    visa_issue_date=visa_issue,
                    visa_expiry_date=visa_expiry,
                    employment_start=employment_start,
                    employment_end=employment_end,
                    entry_date=entry_date,
                )
                workers_batch.append(worker)
                worker_count += 1
                
                # Batch insert
                if len(workers_batch) >= batch_size:
                    db.bulk_save_objects(workers_batch)
                    db.commit()
                    workers_batch = []
                    print(f"    ... {worker_count} workers created", end="\r")
    
    # Insert remaining
    if workers_batch:
        db.bulk_save_objects(workers_batch)
        db.commit()
    
    print(f"  [OK] {worker_count} workers created                    ")


def create_historical_requests(
    db,
    nationality_ids: dict,
    profession_ids: dict,
    establishment_ids: list
) -> None:
    """Create historical request data."""
    print("Creating historical requests...")
    
    # Check existing count
    existing_count = db.query(QuotaRequest).count()
    if existing_count >= 3000:
        print(f"  - {existing_count} requests already exist, skipping")
        return
    
    request_count = 0
    today = date.today()
    
    for nat_code, nat_id in nationality_ids.items():
        if nat_code not in NATIONALITY_PATTERNS:
            continue
            
        tiers = NATIONALITY_PATTERNS[nat_code].get("tiers", {})
        
        # Create ~400-600 requests per nationality over 12 months
        for _ in range(random.randint(400, 600)):
            # Pick profession based on tier distribution
            prof_code = random.choices(
                list(tiers.keys()),
                weights=list(tiers.values()),
                k=1
            )[0]
            
            if prof_code not in profession_ids:
                continue
            
            # Random date in last 12 months
            days_ago = random.randint(1, 365)
            submitted = datetime.combine(
                today - timedelta(days=days_ago),
                datetime.min.time()
            ) + timedelta(hours=random.randint(8, 17))
            
            # Random count (mostly 5-50, occasionally larger)
            count_roll = random.random()
            if count_roll < 0.7:
                count = random.randint(5, 20)
            elif count_roll < 0.95:
                count = random.randint(21, 50)
            else:
                count = random.randint(51, 100)
            
            # Determine status (historical = mostly decided)
            status_roll = random.random()
            if status_roll < 0.75:
                status = RequestStatus.APPROVED
                approved = count
            elif status_roll < 0.85:
                status = RequestStatus.PARTIAL
                approved = int(count * random.uniform(0.3, 0.7))
            elif status_roll < 0.90:
                status = RequestStatus.QUEUED
                approved = 0
            elif status_roll < 0.95:
                status = RequestStatus.BLOCKED
                approved = 0
            else:
                status = RequestStatus.REJECTED
                approved = 0
            
            decided = submitted + timedelta(hours=random.randint(4, 72)) if status != RequestStatus.QUEUED else None
            
            request = QuotaRequest(
                establishment_id=random.choice(establishment_ids),
                nationality_id=nat_id,
                profession_id=profession_ids[prof_code],
                requested_count=count,
                approved_count=approved,
                status=status,
                priority_score=random.randint(-20, 100),
                tier_at_submission=1 if tiers[prof_code] >= 0.15 else 2 if tiers[prof_code] >= 0.05 else 3,
                submitted_date=submitted,
                decided_date=decided,
                decision_reason="Historical request" if status == RequestStatus.APPROVED else "Capacity constraint",
            )
            db.add(request)
            request_count += 1
    
    db.commit()
    print(f"  [OK] {request_count} historical requests created")


def create_queue_entries(db) -> None:
    """Create queue entries for pending/queued requests."""
    print("Creating queue entries...")
    
    queued_requests = db.query(QuotaRequest).filter(
        QuotaRequest.status == RequestStatus.QUEUED
    ).all()
    
    for i, request in enumerate(queued_requests):
        existing = db.query(RequestQueue).filter(
            RequestQueue.request_id == request.id
        ).first()
        
        if existing:
            continue
        
        queue_entry = RequestQueue(
            request_id=request.id,
            queue_position=i + 1,
            tier_at_submission=request.tier_at_submission or 2,
            queued_date=request.submitted_date,
            expiry_date=(request.submitted_date + timedelta(days=90)).date(),
            processing_priority=float(request.priority_score),
        )
        db.add(queue_entry)
    
    db.commit()
    print(f"  [OK] {len(queued_requests)} queue entries created")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Nationality Quota System - Synthetic Data Generation")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    try:
        # Get nationality IDs
        nationalities = db.query(Nationality).all()
        nationality_ids = {n.code: n.id for n in nationalities}
        
        if not nationality_ids:
            print("ERROR: No nationalities found. Run init_db.py first!")
            return
        
        print(f"Found {len(nationality_ids)} nationalities")
        print()
        
        # Create reference data
        profession_ids = create_professions(db)
        print()
        
        activity_ids = create_activities(db)
        print()
        
        establishment_ids = create_establishments(db, activity_ids)
        print()
        
        # Create quota-related data
        create_nationality_caps(db, nationality_ids)
        print()
        
        create_nationality_tiers(db, nationality_ids, profession_ids)
        print()
        
        create_dominance_alerts(db, nationality_ids, profession_ids)
        print()
        
        # Create worker and request data
        create_workers(db, nationality_ids, profession_ids, establishment_ids)
        print()
        
        create_historical_requests(db, nationality_ids, profession_ids, establishment_ids)
        print()
        
        create_queue_entries(db)
        print()
        
        # Print summary
        print("=" * 60)
        print("[OK] Synthetic data generation complete!")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  - Nationalities: {db.query(Nationality).count()}")
        print(f"  - Professions: {db.query(Profession).count()}")
        print(f"  - Activities: {db.query(EconomicActivity).count()}")
        print(f"  - Establishments: {db.query(Establishment).count()}")
        print(f"  - Workers: {db.query(WorkerStock).count()}")
        print(f"  - Requests: {db.query(QuotaRequest).count()}")
        print(f"  - Queue Entries: {db.query(RequestQueue).count()}")
        print(f"  - Dominance Alerts: {db.query(DominanceAlert).count()}")
        print()
        print("Next steps:")
        print("  1. Start API: uvicorn src.api.main:app --reload")
        print("  2. Start UI: streamlit run app/streamlit_app.py")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
