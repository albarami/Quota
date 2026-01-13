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

**Status:** [x] Completed  
**Date Added:** 2026-01-13  
**Date Completed:** 2026-01-13

### 2A: Database Models

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 2.1 | Create src/models/base.py (SQLAlchemy base, engine setup) | [x] | 2026-01-13 |
| 2.2 | Create src/models/core.py (Nationality, Profession, EconomicActivity, Establishment) | [x] | 2026-01-13 |
| 2.3 | Create src/models/quota.py (NationalityCap, NationalityTier, DominanceAlert) | [x] | 2026-01-13 |
| 2.4 | Create src/models/worker.py (WorkerStock with state enum) | [x] | 2026-01-13 |
| 2.5 | Create src/models/request.py (QuotaRequest, RequestQueue, DecisionLog) | [x] | 2026-01-13 |
| 2.6 | Create src/models/config.py (ParameterRegistry) | [x] | 2026-01-13 |
| 2.7 | Create scripts/init_db.py (database initialization) | [x] | 2026-01-13 |

### 2B: Synthetic Data Generation

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 2.8 | Define 11 restricted nationalities with realistic profiles | [x] | 2026-01-13 |
| 2.9 | Define 50+ professions across sectors | [x] | 2026-01-13 |
| 2.10 | Generate 500+ establishments with varying utilization | [x] | 2026-01-13 |
| 2.11 | Generate 150,000+ worker records with visa expiry distribution | [x] | 2026-01-13 |
| 2.12 | Generate tier patterns per nationality (e.g., Egypt 33% Construction) | [x] | 2026-01-13 |
| 2.13 | Generate dominance scenarios (e.g., Egypt 52% in Construction Supervisors) | [x] | 2026-01-13 |
| 2.14 | Generate 12 months historical requests | [x] | 2026-01-13 |
| 2.15 | Generate current queue (200-500 pending items) | [x] | 2026-01-13 |
| 2.16 | Run data validation tests | [x] | 2026-01-13 |
| 2.17 | Git commit: "feat: database models and synthetic data" | [x] | 2026-01-13 |

---

## Phase 3: Business Logic Engines

**Status:** [x] Completed  
**Date Added:** 2026-01-13  
**Date Completed:** 2026-01-13

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 3.1 | Create TierDiscoveryEngine (discover_tiers, get_tier_for_request) | [x] | 2026-01-13 |
| 3.2 | Create CapacityEngine (calculate_effective_headroom, calculate_tier_status, project_outflow) | [x] | 2026-01-13 |
| 3.3 | Create DominanceAlertEngine (check_dominance, calculate_velocity) | [x] | 2026-01-13 |
| 3.4 | Create RequestProcessor (process_request, calculate_priority_score) | [x] | 2026-01-13 |
| 3.5 | Create QueueProcessor (add_to_queue, process_queue_on_capacity_change, revalidate_queue) | [x] | 2026-01-13 |
| 3.6 | Create AIRecommendationEngine (generate_cap_recommendation, explain_decision, suggest_alternatives) | [x] | 2026-01-13 |
| 3.7 | Write unit tests for TierDiscoveryEngine | [x] | 2026-01-13 |
| 3.8 | Write unit tests for CapacityEngine | [x] | 2026-01-13 |
| 3.9 | Write unit tests for DominanceAlertEngine | [x] | 2026-01-13 |
| 3.10 | Write unit tests for RequestProcessor | [x] | 2026-01-13 |
| 3.11 | Write unit tests for QueueProcessor | [x] | 2026-01-13 |
| 3.12 | Git commit: "feat: core business engines" | [x] | 2026-01-13 |

---

## Phase 4: API Layer

**Status:** [x] Completed  
**Date Added:** 2026-01-13  
**Date Completed:** 2026-01-13

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 4.1 | Create src/api/main.py (FastAPI app initialization) | [x] | 2026-01-13 |
| 4.2 | Create Pydantic schemas for all endpoints | [x] | 2026-01-13 |
| 4.3 | Create routes/dashboard.py (GET /dashboard/{nationality}, /dashboard/overview) | [x] | 2026-01-13 |
| 4.4 | Create routes/caps.py (GET/POST caps, AI recommendation endpoint) | [x] | 2026-01-13 |
| 4.5 | Create routes/requests.py (POST request, GET status, GET explain) | [x] | 2026-01-13 |
| 4.6 | Create routes/queue.py (GET queue, POST withdraw) | [x] | 2026-01-13 |
| 4.7 | Create routes/alerts.py (GET alerts, GET critical) | [x] | 2026-01-13 |
| 4.8 | Test all API endpoints | [x] | 2026-01-13 |
| 4.9 | Git commit: "feat: REST API layer" | [x] | 2026-01-13 |

---

## Phase 5: Streamlit Frontend

**Status:** [x] Completed  
**Date Added:** 2026-01-13  
**Date Completed:** 2026-01-13

### 5A: Components & Styling

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 5.1 | Create app/components/styles.py (Qatar theme, CSS) | [x] | 2026-01-13 |
| 5.2 | Create app/components/charts.py (Plotly chart builders) | [x] | 2026-01-13 |
| 5.3 | Create app/components/tables.py (styled data tables) | [x] | 2026-01-13 |
| 5.4 | Create app/components/cards.py (metric cards, status cards) | [x] | 2026-01-13 |

### 5B: Pages

| Task ID | Task | Status | Date Completed |
|---------|------|--------|----------------|
| 5.5 | Create app/streamlit_app.py (main entry, navigation) | [x] | 2026-01-13 |
| 5.6 | Create pages/1_Dashboard.py (live monitoring) | [x] | 2026-01-13 |
| 5.7 | Create pages/2_Cap_Management.py (policymaker view, AI recommendations) | [x] | 2026-01-13 |
| 5.8 | Create pages/3_Request_Portal.py (submit with live eligibility) | [x] | 2026-01-13 |
| 5.9 | Create pages/4_Analytics.py (trends, insights, AI analysis) | [x] | 2026-01-13 |
| 5.10 | Create pages/5_Settings.py (parameter configuration) | [x] | 2026-01-13 |
| 5.11 | Manual UI testing across all pages | [x] | 2026-01-13 |
| 5.12 | Git commit: "feat: Streamlit frontend" | [x] | 2026-01-13 |

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
| 2 | Data Layer & Synthetic Data | 17 | 17 | 100% |
| 3 | Business Logic Engines | 12 | 12 | 100% |
| 4 | API Layer | 9 | 9 | 100% |
| 5 | Streamlit Frontend | 12 | 12 | 100% |
| 6 | Testing | 9 | 0 | 0% |
| 7 | Deployment & Documentation | 8 | 0 | 0% |
| **Total** | | **72** | **65** | **90%** |

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
