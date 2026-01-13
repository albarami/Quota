# Qatar Nationality Quota Allocation System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io/)

A dynamic, demand-driven quota allocation system for restricted nationalities in Qatar's private sector. Built for the Ministry of Labour to manage work permit quotas using intelligent automation.

## Overview

This system manages restricted nationality work permits using three core principles:

1. **Policy-Maker Controlled Caps** - Policymakers set nationality caps; the system manages allocations dynamically
2. **Demand-Driven Tier Discovery** - Automatically classifies professions into tiers based on historical request patterns
3. **Dynamic Capacity Protection** - Protects high-demand professions first, opens lower tiers as capacity allows

### Key Features

- **Real-time Dashboard** - Live monitoring of caps, headroom, tier status, and dominance alerts
- **Auto-Queue System** - Requests automatically processed when capacity opens
- **AI Recommendations** - Azure OpenAI-powered cap recommendations and decision explanations
- **Full Audit Trail** - Every decision logged with complete explainability
- **Professional UI** - Qatar-themed interface suitable for government stakeholders

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+, FastAPI |
| Frontend | Streamlit |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI | Azure OpenAI GPT-4o |
| Charts | Plotly |
| ORM | SQLAlchemy 2.0 |

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Azure OpenAI API access (for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/albarami/Quota.git
   cd Quota
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   
   Create a `.env` file in the project root:
   ```env
   # Azure OpenAI Configuration
   AZURE_OPENAI_API_KEY=your_api_key_here
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   AZURE_OPENAI_DEPLOYMENT=gpt-4o
   
   # Database (optional - defaults to SQLite)
   DATABASE_URL=sqlite:///./data/quota.db
   
   # Debug mode (optional)
   DEBUG=false
   ```

5. **Initialize database with synthetic data**
   ```bash
   python scripts/init_db.py
   python scripts/generate_synthetic_data.py
   ```

### Running the Application

**Start the API server:**
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Start the Streamlit frontend:**
```bash
streamlit run app/streamlit_app.py
```

Access the application at `http://localhost:8501`

## Project Structure

```
Quota/
├── config/                 # Configuration and settings
│   └── settings.py         # Environment and parameter registry
├── src/
│   ├── models/             # SQLAlchemy database models
│   ├── engines/            # Business logic engines
│   │   ├── tier_discovery.py
│   │   ├── capacity.py
│   │   ├── dominance.py
│   │   ├── request_processor.py
│   │   ├── queue_processor.py
│   │   └── ai_engine.py
│   ├── api/                # FastAPI endpoints
│   └── utils/              # Utility functions
├── app/
│   ├── streamlit_app.py    # Main Streamlit entry
│   ├── pages/              # Streamlit pages
│   └── components/         # Reusable UI components
├── scripts/                # Database and data scripts
├── tests/                  # Test suite
├── data/                   # Database and synthetic data
├── PLANNING.md             # Architecture documentation
└── TASK.md                 # Task tracking
```

## Core Concepts

### Tier System

Professions are automatically classified into tiers based on request patterns:

| Tier | Criteria | Approval Mode |
|------|----------|---------------|
| **Tier 1** (Primary) | >15% of requests | Auto-approve if capacity |
| **Tier 2** (Secondary) | 5-15% of requests | Opens when Tier 1 secured |
| **Tier 3** (Minor) | 1-5% of requests | Opens when Tier 1+2 secured |
| **Tier 4** (Unusual) | <1% of requests | Requires justification |

### Capacity Formula

```python
effective_headroom = cap - stock - committed - (pending × 0.8) + (outflow × 0.75)
```

Where:
- `cap` = Policymaker-set nationality cap
- `stock` = Current workers in country
- `committed` = Approved but not yet arrived
- `pending` = Applications under review (80% expected approval)
- `outflow` = Projected departures (75% confidence factor)

### Dominance Alerts

Monitors nationality concentration to prevent over-reliance:

| Alert Level | Share | Action |
|-------------|-------|--------|
| CRITICAL | >50% | Block new approvals |
| HIGH | 40-50% | Partial approve only |
| WATCH | 30-40% | Flag for review |
| OK | <30% | Normal processing |

## API Documentation

When the API server is running, access the interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dashboard/{nationality}` | Live status for nationality |
| GET | `/api/v1/dashboard/overview` | All nationalities summary |
| POST | `/api/v1/requests` | Submit quota request |
| GET | `/api/v1/requests/{id}/explain` | AI explanation of decision |
| GET | `/api/v1/caps/{nationality}/recommendation` | AI cap recommendation |
| GET | `/api/v1/alerts/critical` | All critical dominance alerts |

## Testing

Run the test suite:

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_capacity.py -v
```

## Development

### Code Style

This project uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run formatters:
```bash
black .
isort .
flake8
mypy src/
```

### Git Workflow

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature branches

Commit convention:
- `chore:` - Setup/config changes
- `feat:` - New features
- `fix:` - Bug fixes
- `test:` - Test additions
- `docs:` - Documentation

## Documentation

- [PLANNING.md](PLANNING.md) - System architecture and design decisions
- [TASK.md](TASK.md) - Development task tracking
- [Technical Specification](docs/Nationality_Quota_Formula_v2.docx) - Full system requirements

## License

This project is proprietary software developed for the Qatar Ministry of Labour.

## Support

For issues or questions, contact the development team or open an issue in the GitHub repository.
