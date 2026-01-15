#!/usr/bin/env python
"""
Ministry data import script.

This script imports real ministry data from CSV files into the quota database.
Use this to populate the system with actual data for production deployment.

CSV files should be placed in data/templates/ with the following structure:
    01_nationalities.csv    - Nationality definitions
    02_professions.csv      - Profession/occupation definitions
    03_economic_activities.csv - Economic activity/sector definitions
    04_establishments.csv   - Establishment/employer records
    05_nationality_caps.csv - Annual nationality caps
    06_nationality_tiers.csv - Tier classifications
    07_worker_stock.csv     - Worker records
    08_quota_requests.csv   - Historical quota requests

Usage:
    python scripts/import_ministry_data.py                    # Import all CSVs
    python scripts/import_ministry_data.py --file 07_worker_stock.csv  # Import specific file
    python scripts/import_ministry_data.py --validate         # Validate CSVs only
    python scripts/import_ministry_data.py --clear            # Clear existing data first
"""

import argparse
import csv
import os
import sys
from datetime import date, datetime
from pathlib import Path
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
    WorkerStock,
    WorkerState,
    QuotaRequest,
    RequestStatus,
)

TEMPLATES_DIR = Path(__file__).parent.parent / "data" / "templates"


def parse_bool(value: str) -> bool:
    """Parse boolean from CSV string."""
    return value.lower() in ("true", "1", "yes", "y")


def parse_date(value: str) -> date | None:
    """Parse date from CSV string."""
    if not value or value.strip() == "":
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_datetime(value: str) -> datetime | None:
    """Parse datetime from CSV string."""
    if not value or value.strip() == "":
        return None
    try:
        # Try with time
        return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            # Try date only
            return datetime.strptime(value.strip(), "%Y-%m-%d")
        except ValueError:
            return None


def parse_int(value: str) -> int | None:
    """Parse integer from CSV string."""
    if not value or value.strip() == "":
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None


def parse_float(value: str) -> float | None:
    """Parse float from CSV string."""
    if not value or value.strip() == "":
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None


def read_csv(filepath: Path) -> list[dict[str, str]]:
    """Read CSV file and return list of dictionaries."""
    if not filepath.exists():
        print(f"  [SKIP] File not found: {filepath.name}")
        return []
    
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def import_nationalities(db, rows: list[dict]) -> dict[str, int]:
    """Import nationality records."""
    print("Importing nationalities...")
    id_map = {}
    count = 0
    
    for row in rows:
        code = row.get("code", "").strip()
        if not code:
            continue
        
        # Check if exists
        existing = db.query(Nationality).filter(Nationality.code == code).first()
        if existing:
            id_map[code] = existing.id
            continue
        
        nat = Nationality(
            code=code,
            name=row.get("name", "").strip(),
            name_ar=row.get("name_ar", "").strip() or None,
            is_restricted=parse_bool(row.get("is_restricted", "false")),
            is_gcc=parse_bool(row.get("is_gcc", "false")),
            continent=row.get("continent", "").strip() or None,
        )
        db.add(nat)
        db.flush()
        id_map[code] = nat.id
        count += 1
    
    db.commit()
    print(f"  [OK] {count} nationalities imported, {len(id_map)} total")
    return id_map


def import_professions(db, rows: list[dict]) -> dict[str, int]:
    """Import profession records."""
    print("Importing professions...")
    id_map = {}
    count = 0
    
    for row in rows:
        code = row.get("code", "").strip()
        if not code:
            continue
        
        # Check if exists
        existing = db.query(Profession).filter(Profession.code == code).first()
        if existing:
            id_map[code] = existing.id
            continue
        
        prof = Profession(
            code=code,
            name=row.get("name", "").strip(),
            name_ar=row.get("name_ar", "").strip() or None,
            category=row.get("category", "").strip() or None,
            high_demand_flag=parse_bool(row.get("high_demand_flag", "false")),
            non_skilled_fast_track=parse_bool(row.get("non_skilled_fast_track", "false")),
            description=row.get("description", "").strip() or None,
        )
        db.add(prof)
        db.flush()
        id_map[code] = prof.id
        count += 1
    
    db.commit()
    print(f"  [OK] {count} professions imported, {len(id_map)} total")
    return id_map


def import_activities(db, rows: list[dict]) -> dict[str, int]:
    """Import economic activity records."""
    print("Importing economic activities...")
    id_map = {}
    count = 0
    
    for row in rows:
        code = row.get("code", "").strip()
        if not code:
            continue
        
        # Check if exists
        existing = db.query(EconomicActivity).filter(EconomicActivity.code == code).first()
        if existing:
            id_map[code] = existing.id
            continue
        
        act = EconomicActivity(
            code=code,
            name=row.get("name", "").strip(),
            name_ar=row.get("name_ar", "").strip() or None,
            sector_group=row.get("sector_group", "").strip() or None,
            is_strategic=parse_bool(row.get("is_strategic", "false")),
            strategic_weight=parse_float(row.get("strategic_weight", "1.0")) or 1.0,
        )
        db.add(act)
        db.flush()
        id_map[code] = act.id
        count += 1
    
    db.commit()
    print(f"  [OK] {count} activities imported, {len(id_map)} total")
    return id_map


def import_establishments(db, rows: list[dict], activity_ids: dict[str, int]) -> dict[str, int]:
    """Import establishment records."""
    print("Importing establishments...")
    id_map = {}
    count = 0
    
    for row in rows:
        license_num = row.get("license_number", "").strip()
        if not license_num:
            continue
        
        # Check if exists
        existing = db.query(Establishment).filter(Establishment.license_number == license_num).first()
        if existing:
            id_map[license_num] = existing.id
            continue
        
        activity_code = row.get("activity_code", "").strip()
        activity_id = activity_ids.get(activity_code)
        
        est = Establishment(
            name=row.get("name", "").strip(),
            license_number=license_num,
            activity_id=activity_id,
            total_approved=parse_int(row.get("total_approved", "0")) or 0,
            total_used=parse_int(row.get("total_used", "0")) or 0,
            size_category=row.get("size_category", "").strip() or None,
            is_active=parse_bool(row.get("is_active", "true")),
        )
        db.add(est)
        db.flush()
        id_map[license_num] = est.id
        count += 1
    
    db.commit()
    print(f"  [OK] {count} establishments imported, {len(id_map)} total")
    return id_map


def import_nationality_caps(db, rows: list[dict], nationality_ids: dict[str, int]) -> int:
    """Import nationality cap records."""
    print("Importing nationality caps...")
    count = 0
    
    for row in rows:
        nat_code = row.get("nationality_code", "").strip()
        year = parse_int(row.get("year", ""))
        
        if not nat_code or not year:
            continue
        
        nat_id = nationality_ids.get(nat_code)
        if not nat_id:
            print(f"    [WARN] Nationality not found: {nat_code}")
            continue
        
        # Check if exists
        existing = db.query(NationalityCap).filter(
            NationalityCap.nationality_id == nat_id,
            NationalityCap.year == year
        ).first()
        
        if existing:
            # Update existing
            existing.cap_limit = parse_int(row.get("cap_limit", "0")) or 0
            existing.previous_cap = parse_int(row.get("previous_cap"))
            existing.set_by = row.get("set_by", "").strip() or None
            existing.set_date = parse_date(row.get("set_date")) or date.today()
            existing.notes = row.get("notes", "").strip() or None
        else:
            cap = NationalityCap(
                nationality_id=nat_id,
                year=year,
                cap_limit=parse_int(row.get("cap_limit", "0")) or 0,
                previous_cap=parse_int(row.get("previous_cap")),
                set_by=row.get("set_by", "").strip() or None,
                set_date=parse_date(row.get("set_date")) or date.today(),
                notes=row.get("notes", "").strip() or None,
            )
            db.add(cap)
            count += 1
    
    db.commit()
    print(f"  [OK] {count} nationality caps imported")
    return count


def import_nationality_tiers(
    db,
    rows: list[dict],
    nationality_ids: dict[str, int],
    profession_ids: dict[str, int]
) -> int:
    """Import nationality tier records."""
    print("Importing nationality tiers...")
    count = 0
    
    for row in rows:
        nat_code = row.get("nationality_code", "").strip()
        prof_code = row.get("profession_code", "").strip()
        
        if not nat_code or not prof_code:
            continue
        
        nat_id = nationality_ids.get(nat_code)
        prof_id = profession_ids.get(prof_code)
        
        if not nat_id:
            print(f"    [WARN] Nationality not found: {nat_code}")
            continue
        if not prof_id:
            print(f"    [WARN] Profession not found: {prof_code}")
            continue
        
        # Check if exists (current tier)
        existing = db.query(NationalityTier).filter(
            NationalityTier.nationality_id == nat_id,
            NationalityTier.profession_id == prof_id,
            NationalityTier.valid_to.is_(None)
        ).first()
        
        if existing:
            # Update existing
            existing.tier_level = parse_int(row.get("tier_level", "2")) or 2
            existing.share_pct = parse_float(row.get("share_pct", "0.0")) or 0.0
            existing.request_count = parse_int(row.get("request_count"))
            existing.calculated_date = datetime.utcnow()
        else:
            tier = NationalityTier(
                nationality_id=nat_id,
                profession_id=prof_id,
                tier_level=parse_int(row.get("tier_level", "2")) or 2,
                share_pct=parse_float(row.get("share_pct", "0.0")) or 0.0,
                request_count=parse_int(row.get("request_count")),
                calculated_date=datetime.utcnow(),
                valid_from=parse_date(row.get("valid_from")) or date.today(),
            )
            db.add(tier)
            count += 1
    
    db.commit()
    print(f"  [OK] {count} nationality tiers imported")
    return count


def import_workers(
    db,
    rows: list[dict],
    nationality_ids: dict[str, int],
    profession_ids: dict[str, int],
    establishment_ids: dict[str, int]
) -> int:
    """Import worker stock records."""
    print("Importing workers...")
    count = 0
    batch_size = 1000
    workers_batch = []
    
    state_map = {
        "IN_COUNTRY": WorkerState.IN_COUNTRY,
        "COMMITTED": WorkerState.COMMITTED,
        "PENDING": WorkerState.PENDING,
        "QUEUED": WorkerState.QUEUED,
    }
    
    for row in rows:
        worker_id = row.get("worker_id", "").strip()
        nat_code = row.get("nationality_code", "").strip()
        prof_code = row.get("profession_code", "").strip()
        est_license = row.get("establishment_license", "").strip()
        
        if not nat_code or not prof_code:
            continue
        
        nat_id = nationality_ids.get(nat_code)
        prof_id = profession_ids.get(prof_code)
        est_id = establishment_ids.get(est_license)
        
        if not nat_id or not prof_id:
            continue
        
        # Check if worker exists
        if worker_id:
            existing = db.query(WorkerStock).filter(WorkerStock.worker_id == worker_id).first()
            if existing:
                continue
        
        state_str = row.get("state", "IN_COUNTRY").strip()
        state = state_map.get(state_str, WorkerState.IN_COUNTRY)
        
        worker = WorkerStock(
            worker_id=worker_id or None,
            nationality_id=nat_id,
            profession_id=prof_id,
            establishment_id=est_id or list(establishment_ids.values())[0] if establishment_ids else 1,
            state=state,
            visa_number=row.get("visa_number", "").strip() or None,
            visa_issue_date=parse_date(row.get("visa_issue_date")),
            visa_expiry_date=parse_date(row.get("visa_expiry_date")),
            employment_start=parse_date(row.get("employment_start")),
            employment_end=parse_date(row.get("employment_end")),
            entry_date=parse_date(row.get("entry_date")),
            exit_date=parse_date(row.get("exit_date")),
            is_final_exit=parse_int(row.get("is_final_exit", "0")) or 0,
        )
        workers_batch.append(worker)
        count += 1
        
        if len(workers_batch) >= batch_size:
            db.bulk_save_objects(workers_batch)
            db.commit()
            workers_batch = []
            print(f"    ... {count} workers imported", end="\r")
    
    if workers_batch:
        db.bulk_save_objects(workers_batch)
        db.commit()
    
    print(f"  [OK] {count} workers imported                    ")
    return count


def import_requests(
    db,
    rows: list[dict],
    nationality_ids: dict[str, int],
    profession_ids: dict[str, int],
    establishment_ids: dict[str, int]
) -> int:
    """Import quota request records."""
    print("Importing quota requests...")
    count = 0
    
    status_map = {
        "SUBMITTED": RequestStatus.SUBMITTED,
        "PROCESSING": RequestStatus.PROCESSING,
        "APPROVED": RequestStatus.APPROVED,
        "PARTIAL": RequestStatus.PARTIAL,
        "QUEUED": RequestStatus.QUEUED,
        "BLOCKED": RequestStatus.BLOCKED,
        "REJECTED": RequestStatus.REJECTED,
        "WITHDRAWN": RequestStatus.WITHDRAWN,
        "EXPIRED": RequestStatus.EXPIRED,
    }
    
    for row in rows:
        est_license = row.get("establishment_license", "").strip()
        nat_code = row.get("nationality_code", "").strip()
        prof_code = row.get("profession_code", "").strip()
        
        if not est_license or not nat_code or not prof_code:
            continue
        
        est_id = establishment_ids.get(est_license)
        nat_id = nationality_ids.get(nat_code)
        prof_id = profession_ids.get(prof_code)
        
        if not est_id or not nat_id or not prof_id:
            continue
        
        status_str = row.get("status", "SUBMITTED").strip()
        status = status_map.get(status_str, RequestStatus.SUBMITTED)
        
        request = QuotaRequest(
            establishment_id=est_id,
            nationality_id=nat_id,
            profession_id=prof_id,
            requested_count=parse_int(row.get("requested_count", "0")) or 0,
            approved_count=parse_int(row.get("approved_count", "0")) or 0,
            status=status,
            priority_score=parse_int(row.get("priority_score", "0")) or 0,
            tier_at_submission=parse_int(row.get("tier_at_submission")),
            submitted_date=parse_datetime(row.get("submitted_date")) or datetime.utcnow(),
            decided_date=parse_datetime(row.get("decided_date")),
            decision_reason=row.get("decision_reason", "").strip() or None,
        )
        db.add(request)
        count += 1
    
    db.commit()
    print(f"  [OK] {count} quota requests imported")
    return count


def validate_csvs() -> bool:
    """Validate all CSV files exist and have required columns."""
    print("Validating CSV files...")
    
    required_files = {
        "01_nationalities.csv": ["code", "name"],
        "02_professions.csv": ["code", "name"],
        "03_economic_activities.csv": ["code", "name"],
        "04_establishments.csv": ["name", "license_number"],
        "05_nationality_caps.csv": ["nationality_code", "year", "cap_limit"],
        "06_nationality_tiers.csv": ["nationality_code", "profession_code", "tier_level"],
        "07_worker_stock.csv": ["nationality_code", "profession_code"],
        "08_quota_requests.csv": ["establishment_license", "nationality_code", "profession_code"],
    }
    
    all_valid = True
    
    for filename, required_cols in required_files.items():
        filepath = TEMPLATES_DIR / filename
        if not filepath.exists():
            print(f"  [MISS] {filename}")
            continue
        
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            
            missing = [col for col in required_cols if col not in headers]
            if missing:
                print(f"  [FAIL] {filename} - missing columns: {missing}")
                all_valid = False
            else:
                row_count = sum(1 for _ in reader)
                print(f"  [OK] {filename} ({row_count} rows)")
    
    return all_valid


def clear_data(db) -> None:
    """Clear all data from the database (preserving parameters)."""
    print("Clearing existing data...")
    
    # Clear in reverse order of dependencies
    db.query(QuotaRequest).delete()
    db.query(WorkerStock).delete()
    db.query(NationalityTier).delete()
    db.query(NationalityCap).delete()
    db.query(Establishment).delete()
    db.query(EconomicActivity).delete()
    db.query(Profession).delete()
    db.query(Nationality).delete()
    
    db.commit()
    print("  [OK] All data cleared")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Import ministry data from CSV files")
    parser.add_argument(
        "--file",
        type=str,
        help="Import specific CSV file only"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate CSV files without importing"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before importing"
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("Nationality Quota System - Ministry Data Import")
    print("=" * 60)
    print()
    print(f"Templates directory: {TEMPLATES_DIR}")
    print()
    
    # Validate mode
    if args.validate:
        valid = validate_csvs()
        if valid:
            print("\n[OK] All CSV files are valid")
        else:
            print("\n[ERROR] Some CSV files have issues")
        return
    
    db = SessionLocal()
    try:
        # Clear data if requested
        if args.clear:
            print("WARNING: This will delete all existing data!")
            confirm = input("Type 'yes' to confirm: ")
            if confirm.lower() != "yes":
                print("Aborted.")
                return
            clear_data(db)
            print()
        
        # Import data
        if args.file:
            # Import single file
            filepath = TEMPLATES_DIR / args.file
            if not filepath.exists():
                print(f"[ERROR] File not found: {args.file}")
                return
            
            # Need to load dependencies first for single file imports
            nat_ids = {n.code: n.id for n in db.query(Nationality).all()}
            prof_ids = {p.code: p.id for p in db.query(Profession).all()}
            act_ids = {a.code: a.id for a in db.query(EconomicActivity).all()}
            est_ids = {e.license_number: e.id for e in db.query(Establishment).all()}
            
            rows = read_csv(filepath)
            
            if "nationalities" in args.file:
                import_nationalities(db, rows)
            elif "professions" in args.file:
                import_professions(db, rows)
            elif "activities" in args.file:
                import_activities(db, rows)
            elif "establishments" in args.file:
                import_establishments(db, rows, act_ids)
            elif "caps" in args.file:
                import_nationality_caps(db, rows, nat_ids)
            elif "tiers" in args.file:
                import_nationality_tiers(db, rows, nat_ids, prof_ids)
            elif "worker" in args.file:
                import_workers(db, rows, nat_ids, prof_ids, est_ids)
            elif "request" in args.file:
                import_requests(db, rows, nat_ids, prof_ids, est_ids)
        else:
            # Import all files in order
            nat_rows = read_csv(TEMPLATES_DIR / "01_nationalities.csv")
            nat_ids = import_nationalities(db, nat_rows)
            print()
            
            prof_rows = read_csv(TEMPLATES_DIR / "02_professions.csv")
            prof_ids = import_professions(db, prof_rows)
            print()
            
            act_rows = read_csv(TEMPLATES_DIR / "03_economic_activities.csv")
            act_ids = import_activities(db, act_rows)
            print()
            
            est_rows = read_csv(TEMPLATES_DIR / "04_establishments.csv")
            est_ids = import_establishments(db, est_rows, act_ids)
            print()
            
            cap_rows = read_csv(TEMPLATES_DIR / "05_nationality_caps.csv")
            import_nationality_caps(db, cap_rows, nat_ids)
            print()
            
            tier_rows = read_csv(TEMPLATES_DIR / "06_nationality_tiers.csv")
            import_nationality_tiers(db, tier_rows, nat_ids, prof_ids)
            print()
            
            worker_rows = read_csv(TEMPLATES_DIR / "07_worker_stock.csv")
            import_workers(db, worker_rows, nat_ids, prof_ids, est_ids)
            print()
            
            request_rows = read_csv(TEMPLATES_DIR / "08_quota_requests.csv")
            import_requests(db, request_rows, nat_ids, prof_ids, est_ids)
            print()
        
        # Print summary
        print("=" * 60)
        print("[OK] Import complete!")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  - Nationalities: {db.query(Nationality).count()}")
        print(f"  - Professions: {db.query(Profession).count()}")
        print(f"  - Activities: {db.query(EconomicActivity).count()}")
        print(f"  - Establishments: {db.query(Establishment).count()}")
        print(f"  - Workers: {db.query(WorkerStock).count()}")
        print(f"  - Requests: {db.query(QuotaRequest).count()}")
        print()
        print("Next steps:")
        print("  1. Start API: uvicorn src.api.main:app --reload")
        print("  2. Start UI: streamlit run app/streamlit_app.py")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
