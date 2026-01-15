# Ministry Data Templates

This folder contains CSV templates for importing real ministry data into the Nationality Quota System.

## Quick Start

1. **Populate the CSV files** with real ministry data (replacing sample data)
2. **Initialize the database**: `python scripts/init_db.py`
3. **Import the data**: `python scripts/import_ministry_data.py`
4. **Start the system**: `streamlit run app/streamlit_app.py`

## CSV Files

Import files in numerical order (dependencies are handled automatically):

| File | Description | Key Columns |
|------|-------------|-------------|
| `01_nationalities.csv` | Country/nationality definitions | code, name, is_restricted |
| `02_professions.csv` | Job/occupation definitions | code, name, category, high_demand_flag |
| `03_economic_activities.csv` | Industry/sector classifications | code, name, is_strategic |
| `04_establishments.csv` | Employer/company records | license_number, name, activity_code |
| `05_nationality_caps.csv` | Annual nationality caps | nationality_code, year, cap_limit |
| `06_nationality_tiers.csv` | Tier classifications | nationality_code, profession_code, tier_level |
| `07_worker_stock.csv` | Worker records | worker_id, nationality_code, profession_code, state |
| `08_quota_requests.csv` | Historical quota requests | establishment_license, nationality_code, requested_count |

## Column Specifications

### 01_nationalities.csv
```
code          - ISO 3-letter country code (e.g., EGY, IND, PAK)
name          - Full nationality name in English
name_ar       - Full nationality name in Arabic (optional)
is_restricted - Whether this nationality has quota restrictions (true/false)
is_gcc        - Whether this is a GCC country (true/false)
continent     - Continent name (Asia, Africa, etc.)
```

### 02_professions.csv
```
code                  - Unique profession code (e.g., CONST_SUP, SW_DEV)
name                  - Profession name in English
name_ar               - Profession name in Arabic (optional)
category              - Category (Construction, IT, Healthcare, etc.)
high_demand_flag      - High-demand skill - adds +50 priority (true/false)
non_skilled_fast_track - Eligible for fast-track processing (true/false)
description           - Detailed description (optional)
```

### 03_economic_activities.csv
```
code            - Unique activity code (e.g., CONST, IT_SERVICES)
name            - Activity name in English
name_ar         - Activity name in Arabic (optional)
sector_group    - High-level sector grouping
is_strategic    - Strategic sector - adds +30 priority (true/false)
strategic_weight - Weight multiplier (1.0 for normal, 1.5 for strategic)
```

### 04_establishments.csv
```
name           - Establishment/company name
license_number - Business license number (unique identifier)
activity_code  - Foreign key to economic_activities.code
total_approved - Total approved labor quota
total_used     - Currently used labor quota
size_category  - Size classification (Small, Medium, Large)
is_active      - Whether establishment is active (true/false)
```

### 05_nationality_caps.csv
```
nationality_code - Foreign key to nationalities.code
year            - Year the cap applies to (e.g., 2026)
cap_limit       - Maximum workers allowed
previous_cap    - Previous year's cap (for growth calculation)
set_by          - Who set this cap (e.g., "Policy Committee")
set_date        - When the cap was set (YYYY-MM-DD)
notes           - Additional notes or rationale
```

### 06_nationality_tiers.csv
```
nationality_code - Foreign key to nationalities.code
profession_code  - Foreign key to professions.code
tier_level       - Tier classification:
                   1 = Primary (>15% of requests)
                   2 = Secondary (5-15% of requests)
                   3 = Minor (1-5% of requests)
                   4 = Unusual (<1% of requests)
share_pct        - Percentage of requests (0.0 to 1.0)
request_count    - Number of requests in calculation period
valid_from       - Start of validity period (YYYY-MM-DD)
```

### 07_worker_stock.csv
```
worker_id            - Unique worker identifier
nationality_code     - Foreign key to nationalities.code
profession_code      - Foreign key to professions.code
establishment_license - Foreign key to establishments.license_number
state                - Worker state:
                       IN_COUNTRY = Active, in Qatar
                       COMMITTED = Approved, not yet arrived
                       PENDING = Under review
                       QUEUED = Waiting for capacity
visa_number          - Visa reference number
visa_issue_date      - When visa was issued (YYYY-MM-DD)
visa_expiry_date     - When visa expires (YYYY-MM-DD)
employment_start     - Employment start date (YYYY-MM-DD)
employment_end       - Expected employment end date (YYYY-MM-DD)
entry_date           - Date of entry to Qatar (YYYY-MM-DD)
exit_date            - Date of exit from Qatar (YYYY-MM-DD, if departed)
is_final_exit        - Whether exit is permanent (0 or 1)
```

### 08_quota_requests.csv
```
establishment_license - Foreign key to establishments.license_number
nationality_code      - Foreign key to nationalities.code
profession_code       - Foreign key to professions.code
requested_count       - Number of workers requested
approved_count        - Number actually approved
status                - Request status:
                        SUBMITTED, PROCESSING, APPROVED, PARTIAL,
                        QUEUED, BLOCKED, REJECTED, WITHDRAWN, EXPIRED
priority_score        - Calculated priority score
tier_at_submission    - Tier level when request was submitted
submitted_date        - When request was submitted (YYYY-MM-DD HH:MM:SS)
decided_date          - When decision was made (YYYY-MM-DD HH:MM:SS)
decision_reason       - Human-readable decision explanation
```

## Import Commands

```bash
# Validate CSV files (check format without importing)
python scripts/import_ministry_data.py --validate

# Import all CSV files
python scripts/import_ministry_data.py

# Import specific file only
python scripts/import_ministry_data.py --file 07_worker_stock.csv

# Clear existing data and re-import
python scripts/import_ministry_data.py --clear
```

## Data Guidelines

### For Production Deployment

1. **Replace sample data** with actual ministry data from LMIS
2. **Worker Stock**: Export from VRSP_VISA_DTL_ACTIVE and EMPLOYMENT tables
3. **Establishments**: Export from company registration system
4. **Caps**: Set based on policy decisions
5. **Tiers**: Can be auto-calculated from historical request data

### Important Notes

- All date fields use format: `YYYY-MM-DD`
- All datetime fields use format: `YYYY-MM-DD HH:MM:SS`
- Boolean fields accept: `true`, `false`, `1`, `0`, `yes`, `no`
- Percentage fields (share_pct) use decimal format: `0.15` = 15%
- Empty cells are treated as NULL
- UTF-8 encoding is required (supports Arabic text)

## Support

For questions about data format or import issues, contact the Digital Transformation Office.
