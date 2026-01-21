# 🇶🇦 Qatar Nationality Quota Allocation System

A dynamic, demand-driven quota allocation system for restricted nationalities in Qatar's private sector workforce.

## Overview

This system implements Qatar's Ministry of Labour nationality quota policy, providing:

- **Dynamic Tier Discovery**: Automatically classifies professions into tiers based on historical demand patterns
- **Real-time Capacity Engine**: Calculates effective headroom using the golden formula
- **Dominance Alerts**: Monitors and prevents over-concentration of nationalities in professions
- **Auto-Queue Processing**: Intelligent request queuing with automatic processing when capacity opens
- **AI Recommendations**: Azure OpenAI-powered cap recommendations and decision explanations

## The Golden Formula

```python
effective_headroom = cap - stock - committed - (pending × 0.8) + (outflow × 0.75)
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+ / FastAPI |
| Frontend | Streamlit |
| Database | SQLite (demo) / PostgreSQL (production) |
| AI | OpenAI / Azure OpenAI |
| Charts | Plotly |
| Validation | Pydantic |

## Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/albarami/Quota.git
cd Quota

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=sqlite:///data/quota.db

# OpenAI API Key (works with both regular OpenAI and Azure OpenAI)
OPENAI_API_KEY=your_key_here

# Azure OpenAI (optional - only needed if using Azure instead of regular OpenAI)
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_DEPLOYMENT=gpt-4
# AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

For **Streamlit Cloud**, add `OPENAI_API_KEY` in your app secrets.

### 3. Initialize Database

```bash
python scripts/init_db.py
python scripts/generate_synthetic_data.py
```

### 4. Run the Application

**Start the API server:**
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Start the Streamlit frontend:**
```bash
streamlit run app/streamlit_app.py
```

Access:
- API Documentation: http://localhost:8000/docs
- Streamlit Dashboard: http://localhost:8501

## Project Structure

```
Quota/
├── app/                    # Streamlit frontend
│   ├── components/         # UI components (styles, charts, cards)
│   ├── pages/              # Multi-page Streamlit app
│   └── streamlit_app.py    # Main entry point
├── config/                 # Configuration
│   └── settings.py         # Environment and parameters
├── data/                   # Database and synthetic data
├── docs/                   # Documentation
├── scripts/                # Utility scripts
│   ├── init_db.py          # Database initialization
│   └── generate_synthetic_data.py
├── src/                    # Core application
│   ├── api/                # FastAPI routes and schemas
│   ├── engines/            # Business logic engines
│   └── models/             # SQLAlchemy models
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── PLANNING.md             # Architecture documentation
├── TASK.md                 # Task tracking
└── requirements.txt        # Dependencies
```

## Core Engines

### 1. TierDiscoveryEngine
Discovers demand patterns per nationality from historical data.
- Tier 1 (Primary): >15% of requests
- Tier 2 (Secondary): 5-15% of requests
- Tier 3 (Minor): 1-5% of requests
- Tier 4 (Unusual): <1% of requests

### 2. CapacityEngine
Real-time calculation of headroom and tier availability.
- Effective headroom formula
- Tier status cascade
- Outflow projections

### 3. DominanceAlertEngine
Monitors nationality concentration within professions.
- CRITICAL: >50% share → Blocks approvals
- HIGH: 40-50% share → Partial only
- WATCH: 30-40% share → Flagged for review
- OK: <30% share → Normal processing

### 4. RequestProcessor
Main decision engine with complete rule chain.
- Priority scoring
- Decision logging
- Alternative suggestions

### 5. QueueProcessor
Manages the auto-queue with 90-day expiry.
- Priority-weighted FIFO processing
- 30-day confirmation requirement
- Automatic revalidation

### 6. AIRecommendationEngine
Azure OpenAI integration for intelligent recommendations.
- Cap recommendations with rationale
- Decision explanations
- Market trend analysis

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/dashboard/{code}` | GET | Dashboard data for nationality |
| `/api/v1/caps` | GET | List all caps |
| `/api/v1/caps/{code}` | GET/POST | Get/set cap |
| `/api/v1/caps/{code}/recommendation` | GET | AI cap recommendation |
| `/api/v1/requests` | POST | Submit request |
| `/api/v1/requests/check-eligibility` | POST | Pre-check eligibility |
| `/api/v1/queue/{code}` | GET | Queue status |
| `/api/v1/alerts/{code}` | GET | Dominance alerts |

## Key Business Rules

1. **Outflow = FINAL EXITS ONLY** (not vacation travel)
2. **Pipeline Commitments**: Subtract COMMITTED and PENDING from headroom
3. **Confidence Factor**: Apply 0.75 to outflow projections
4. **Cap Calculation Period**: 6-month rolling basis (180 days)
5. **Queue Expiry**: 90 days, confirmation required at day 30
6. **Dominance MIN_PROFESSION_SIZE**: 200 (rules apply only above this)
7. **Tier Hysteresis**: ±2% to prevent oscillation

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Restricted Nationalities

The system manages quotas for 12 restricted nationalities:
- Egypt (EGY)
- India (IND)
- Pakistan (PAK)
- Nepal (NPL)
- Bangladesh (BGD)
- Philippines (PHL)
- Sri Lanka (LKA)
- Iran (IRN)
- Iraq (IRQ)
- Yemen (YEM)
- Syria (SYR)
- Afghanistan (AFG)

## Ministry Data Upload Instructions

When the ministry uploads new worker data, run the following command to regenerate the summary with correct formulas:

```bash
# Step 1: Place the new CSV files in the real_data/ folder
# Required files:
#   - 07_worker_stock.csv (main worker data)
#   - 01_nationalities.csv (nationality reference)
#   - 02_professions.csv (profession reference)
#   - 05_nationality_caps.csv (cap limits)

# Step 2: Regenerate the summary with correct formulas
python scripts/create_data_summary.py

# Step 3: Verify all formulas match documentation
python scripts/verify_all_formulas.py
```

### What the Summary Generation Does

The `create_data_summary.py` script implements all formulas from `System_Documentation.md`:

1. **Tier Classification** (Section 4): `tier_share = workers_in_profession / total_workers_of_nationality`
2. **Dominance Alerts** (Section 6): `dominance_share = nationality_workers / total_workers_in_profession`
3. **Headroom** (Section 5): `cap - stock - committed - (pending × 0.8) + (outflow × 0.75)`
4. **Utilization** (Section 5): `(stock / cap) × 100`

### Important Notes

- **MIN_PROFESSION_SIZE = 200**: Dominance alerts only apply to professions with 200+ total workers
- The summary file (`real_data/summary_by_nationality.json`) is used by Streamlit Cloud for fast loading
- After regenerating, commit and push to update the cloud deployment

## License

© 2026 Qatar Ministry of Labour. All rights reserved.

## Contact

For questions or support, contact the Ministry of Labour Digital Transformation Office.
