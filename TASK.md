# TASK.md - Nationality Quota Allocation System

## Project Info

- **Project:** Qatar Ministry of Labour - Nationality Quota Allocation System
- **Start Date:** 2026-01-13
- **Repository:** https://github.com/albarami/Quota
- **Status:** In Progress

---

## Phase 1: Environment Setup

**Status:** [x] Completed  
**Date Added:** 2026-01-13  
**Date Completed:** 2026-01-13

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 1.1 | Create .gitignore (Python, env, IDE, data files) | [x] | 2026-01-13 |
| 1.2 | Create requirements.txt with all dependencies | [x] | 2026-01-13 |
| 1.3 | Create config/settings.py with env loading and parameter defaults | [x] | 2026-01-13 |
| 1.4 | Create README.md with project overview | [x] | 2026-01-13 |
| 1.5 | Initial git commit and push | [x] | 2026-01-13 |

---

## Phase 2: Data Layer & Synthetic Data

**Status:** [ ] Not Started  
**Date Added:** 2026-01-13

### 2A: Database Models

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 2.1 | Create src/models/base.py (SQLAlchemy base, engine setup) | [ ] | |
| 2.2 | Create src/models/core.py (Nationality, Profession, EconomicActivity, Establishment) | [ ] | |
| 2.3 | Create src/models/quota.py (NationalityCap, NationalityTier, DominanceAlert) | [ ] | |
| 2.4 | Create src/models/worker.py (WorkerStock with state enum) | [ ] | |
| 2.5 | Create src/models/request.py (QuotaRequest, RequestQueue, DecisionLog) | [ ] | |
| 2.6 | Create src/models/config.py (ParameterRegistry) | [ ] | |
| 2.7 | Create scripts/init_db.py (database initialization) | [ ] | |

### 2B: Synthetic Data Generation

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 2.8 | Define 11 restricted nationalities with realistic profiles | [ ] | |
| 2.9 | Define 50+ professions across sectors | [ ] | |
| 2.10 | Generate 500+ establishments with varying utilization | [ ] | |
| 2.11 | Generate 150,000+ worker records with visa expiry distribution | [ ] | |
| 2.12 | Generate tier patterns per nationality (e.g., Egypt 33% Construction) | [ ] | |
| 2.13 | Generate dominance scenarios (e.g., Egypt 52% in Construction Supervisors) | [ ] | |
| 2.14 | Generate 12 months historical requests | [ ] | |
| 2.15 | Generate current queue (200-500 pending items) | [ ] | |
| 2.16 | Run data validation tests | [ ] | |
| 2.17 | Git commit: "feat: database models and synthetic data" | [ ] | |

---

## Phase 3: Business Logic Engines

**Status:** [ ] Not Started  
**Date Added:** 2026-01-13

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 3.1 | Create TierDiscoveryEngine (discover_tiers, get_tier_for_request) | [ ] | |
| 3.2 | Create CapacityEngine (calculate_effective_headroom, calculate_tier_status, project_outflow) | [ ] | |
| 3.3 | Create DominanceAlertEngine (check_dominance, calculate_velocity) | [ ] | |
| 3.4 | Create RequestProcessor (process_request, calculate_priority_score) | [ ] | |
| 3.5 | Create QueueProcessor (add_to_queue, process_queue_on_capacity_change, revalidate_queue) | [ ] | |
| 3.6 | Create AIRecommendationEngine (generate_cap_recommendation, explain_decision, suggest_alternatives) | [ ] | |
| 3.7 | Write unit tests for TierDiscoveryEngine | [ ] | |
| 3.8 | Write unit tests for CapacityEngine | [ ] | |
| 3.9 | Write unit tests for DominanceAlertEngine | [ ] | |
| 3.10 | Write unit tests for RequestProcessor | [ ] | |
| 3.11 | Write unit tests for QueueProcessor | [ ] | |
| 3.12 | Git commit: "feat: core business engines" | [ ] | |

---

## Phase 4: API Layer

**Status:** [ ] Not Started  
**Date Added:** 2026-01-13

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 4.1 | Create src/api/main.py (FastAPI app initialization) | [ ] | |
| 4.2 | Create Pydantic schemas for all endpoints | [ ] | |
| 4.3 | Create routes/dashboard.py (GET /dashboard/{nationality}, /dashboard/overview) | [ ] | |
| 4.4 | Create routes/caps.py (GET/POST caps, AI recommendation endpoint) | [ ] | |
| 4.5 | Create routes/requests.py (POST request, GET status, GET explain) | [ ] | |
| 4.6 | Create routes/queue.py (GET queue, POST withdraw) | [ ] | |
| 4.7 | Create routes/alerts.py (GET alerts, GET critical) | [ ] | |
| 4.8 | Test all API endpoints | [ ] | |
| 4.9 | Git commit: "feat: REST API layer" | [ ] | |

---

## Phase 5: Streamlit Frontend

**Status:** [ ] Not Started  
**Date Added:** 2026-01-13

### 5A: Components & Styling

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 5.1 | Create app/components/styles.py (Qatar theme, CSS) | [ ] | |
| 5.2 | Create app/components/charts.py (Plotly chart builders) | [ ] | |
| 5.3 | Create app/components/tables.py (styled data tables) | [ ] | |
| 5.4 | Create app/components/cards.py (metric cards, status cards) | [ ] | |

### 5B: Pages

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 5.5 | Create app/streamlit_app.py (main entry, navigation) | [ ] | |
| 5.6 | Create pages/1_Dashboard.py (live monitoring) | [ ] | |
| 5.7 | Create pages/2_Cap_Management.py (policymaker view, AI recommendations) | [ ] | |
| 5.8 | Create pages/3_Request_Portal.py (submit with live eligibility) | [ ] | |
| 5.9 | Create pages/4_Analytics.py (trends, insights, AI analysis) | [ ] | |
| 5.10 | Create pages/5_Settings.py (parameter configuration) | [ ] | |
| 5.11 | Manual UI testing across all pages | [ ] | |
| 5.12 | Git commit: "feat: Streamlit frontend" | [ ] | |

---

## Phase 6: Testing

**Status:** [ ] Not Started  
**Date Added:** 2026-01-13

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 6.1 | Create tests/conftest.py (fixtures, test database) | [ ] | |
| 6.2 | Integration test: Full request approval flow | [ ] | |
| 6.3 | Integration test: Request -> Queue -> Auto-approval | [ ] | |
| 6.4 | Integration test: Dominance block with alternatives | [ ] | |
| 6.5 | Edge case: Cap reached mid-request | [ ] | |
| 6.6 | Edge case: Concurrent requests same nationality | [ ] | |
| 6.7 | Edge case: Dominance change while in queue | [ ] | |
| 6.8 | Run full test suite, ensure all pass | [ ] | |
| 6.9 | Git commit: "test: comprehensive test suite" | [ ] | |

---

## Phase 7: Deployment & Documentation

**Status:** [ ] Not Started  
**Date Added:** 2026-01-13

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 7.1 | Create app/.streamlit/config.toml | [ ] | |
| 7.2 | Configure Streamlit Cloud secrets | [ ] | |
| 7.3 | Update README.md with full documentation | [ ] | |
| 7.4 | Add screenshots to documentation | [ ] | |
| 7.5 | Create user guide for each role | [ ] | |
| 7.6 | Final code review and cleanup | [ ] | |
| 7.7 | Git commit: "docs: deployment ready" | [ ] | |
| 7.8 | Deploy to Streamlit Cloud | [ ] | |

---

## Discovered During Work

*Tasks discovered during implementation will be added here*

| Task ID | Task | Phase | Status | Date Added |
|---------|------|-------|--------|------------|
| | | | | |

---

## Completed Summary

| Phase | Description | Tasks | Completed | Percentage |
|-------|-------------|-------|-----------|------------|
| 1 | Environment Setup | 5 | 5 | 100% |
| 2 | Data Layer & Synthetic Data | 17 | 0 | 0% |
| 3 | Business Logic Engines | 12 | 0 | 0% |
| 4 | API Layer | 9 | 0 | 0% |
| 5 | Streamlit Frontend | 12 | 0 | 0% |
| 6 | Testing | 9 | 0 | 0% |
| 7 | Deployment & Documentation | 8 | 0 | 0% |
| **Total** | | **72** | **5** | **7%** |

---

## Notes

### Key Business Rules to Remember

1. **Outflow = FINAL EXITS ONLY** (not vacation travel, Ramadan visits, business trips)
2. **Pipeline Commitments:** Must subtract COMMITTED and PENDING from headroom
3. **Confidence Factor:** Apply 0.75 to outflow projections
4. **Queue Expiry:** 90 days, with confirmation required at day 30
5. **Dominance MIN_PROFESSION_SIZE:** 200 (don't apply to small professions)
6. **Tier Hysteresis:** ±2% to prevent oscillation

### The Golden Formula

```python
effective_headroom = cap - stock - committed - (pending × 0.8) + (outflow × 0.75)
```

### Commit Convention

- `chore:` - Setup/config changes
- `feat:` - New features
- `fix:` - Bug fixes
- `test:` - Test additions
- `docs:` - Documentation
