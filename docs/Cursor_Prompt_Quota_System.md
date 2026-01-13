# Cursor IDE Prompt: Build Nationality Quota Allocation System

## Project Context

I have a technical specification document for a **Dynamic Nationality Quota Allocation System** for Qatar's Ministry of Labour. The system manages restricted nationality work permits using:

- **Dynamic Tier Discovery**: Learns demand patterns from historical data (Tier 1-4)
- **Capacity Engine**: Real-time headroom calculation with pipeline commitments
- **Auto-Queue**: Requests queued when tiers closed, auto-processed when capacity opens
- **Dominance Alerts**: Prevents nationality concentration in professions
- **Live Dashboard**: Real-time monitoring with projections

**Tech Stack:**
- Backend: Python (FastAPI or Flask)
- Frontend: Streamlit Cloud
- Database: SQLite (for demo) / PostgreSQL-ready
- AI: Azure OpenAI for interpretations and recommendations
- Version Control: GitHub (https://github.com/albarami/Quota)

**Environment:**
- Project folder: `D:/Quota`
- `.env` file contains Azure OpenAI API key

---

## MASTER PROMPT FOR CURSOR

```
I need you to build a complete Nationality Quota Allocation System based on the technical specification document I've shared. This is a sophisticated labor market management system for Qatar's Ministry of Labour.

Before we begin, please read and thoroughly understand the technical specification document. Then we will proceed in phases, with you adopting the appropriate expert persona for each phase.

## PHASE 0: PLANNING & ARCHITECTURE
**🎭 Act as: Senior Solutions Architect & Technical Lead**

Before writing any code, create a detailed implementation plan:

1. **System Architecture Diagram** (describe in text/mermaid)
   - Data layer (models, relationships)
   - Business logic layer (engines: Tier Discovery, Capacity, Queue Processor)
   - API layer (endpoints)
   - Presentation layer (Streamlit)
   - AI integration layer (Azure OpenAI)

2. **Database Schema Design**
   - All tables needed based on the spec
   - Relationships and foreign keys
   - Indexes for performance

3. **Project Structure**
   ```
   D:/Quota/
   ├── .env
   ├── .gitignore
   ├── requirements.txt
   ├── README.md
   ├── config/
   │   └── settings.py
   ├── data/
   │   ├── synthetic/
   │   └── migrations/
   ├── src/
   │   ├── __init__.py
   │   ├── models/
   │   ├── engines/
   │   ├── api/
   │   └── utils/
   ├── app/
   │   ├── streamlit_app.py
   │   ├── pages/
   │   └── components/
   ├── tests/
   └── scripts/
   ```

4. **Development Phases Breakdown** with estimated complexity
5. **Git branching strategy** (feature branches → main)

Output the complete plan, then wait for my approval before proceeding.

---

## PHASE 1: ENVIRONMENT SETUP
**🎭 Act as: DevOps Engineer & Python Environment Specialist**

Set up the professional development environment:

1. **Create `.gitignore`** (Python, env, IDE files, data files)

2. **Create `requirements.txt`** with all dependencies:
   - fastapi, uvicorn (API)
   - streamlit (Frontend)
   - sqlalchemy, alembic (Database)
   - pandas, numpy (Data processing)
   - openai, azure-identity (Azure OpenAI)
   - python-dotenv (Environment)
   - pydantic (Validation)
   - plotly (Charts)
   - pytest (Testing)

3. **Create `config/settings.py`**:
   - Load environment variables
   - Azure OpenAI configuration
   - Database connection settings
   - Application constants (thresholds from Parameter Registry)

4. **Create `README.md`** with:
   - Project description
   - Setup instructions
   - Architecture overview
   - How to run

After creating these files:
```bash
git add .
git commit -m "chore: initial project setup with environment configuration"
git push origin main
```

---

## PHASE 2: DATA LAYER & SYNTHETIC DATA
**🎭 Act as: Senior Data Engineer & Database Architect**

Build the data foundation:

### 2.1 Database Models (`src/models/`)

Create SQLAlchemy models for:

```python
# Core Entities (from LMIS)
- Nationality (id, code, name, is_restricted, is_gcc, continent)
- Profession (id, code, name, high_demand_flag, non_skilled_fast_track)
- EconomicActivity (id, code, name, sector_group, strategic_weight)
- Establishment (id, name, activity_id, total_approved, total_used)

# Quota Management
- NationalityCap (id, nationality_id, year, cap_limit, set_by, set_date)
- NationalityTier (id, nationality_id, profession_id, tier_level, share_pct, calculated_date)
- DominanceAlert (id, nationality_id, profession_id, share_pct, velocity, alert_level, created_date)

# Worker Tracking (State Model from spec)
- WorkerStock (id, nationality_id, profession_id, establishment_id, state, visa_expiry, employment_end)
  # state: IN_COUNTRY, COMMITTED, PENDING, QUEUED

# Request Processing
- QuotaRequest (id, establishment_id, nationality_id, profession_id, requested_count, 
                status, priority_score, submitted_date, decided_date, decision_reason)
- RequestQueue (id, request_id, queue_position, tier_at_submission, queued_date, 
                expiry_date, last_revalidation)

# Audit & Logging
- DecisionLog (id, request_id, decision, tier_status_snapshot, capacity_snapshot, 
               dominance_snapshot, priority_score, rule_chain, parameter_version, 
               override_flag, override_authority, created_at)

# Configuration
- ParameterRegistry (id, parameter_name, value, category, valid_from, valid_to, changed_by)
```

### 2.2 Synthetic Data Generation (`scripts/generate_synthetic_data.py`)

**🎭 Act as: Data Scientist specializing in Synthetic Data Generation**

Create realistic synthetic data for Qatar's labor market:

**Nationalities (Restricted):**
| Code | Name | Typical Professions | Approximate Stock |
|------|------|---------------------|-------------------|
| EGY | Egypt | Construction, Engineering, Drivers | 8,500 |
| IND | India | IT, Construction, Retail | 45,000 |
| PAK | Pakistan | Construction, Security, Drivers | 25,000 |
| NPL | Nepal | Security, Hospitality, Construction | 35,000 |
| BGD | Bangladesh | Construction, Manufacturing | 28,000 |
| PHL | Philippines | Healthcare, Hospitality, Domestic | 22,000 |
| IRN | Iran | Engineering, Medical, Academic | 3,200 |
| IRQ | Iraq | Drivers, Security, Labor | 2,800 |
| YEM | Yemen | Retail, Drivers, Security | 1,500 |
| SYR | Syria | Hospitality, Retail, Drivers | 2,200 |
| AFG | Afghanistan | Security, Labor | 1,800 |

**Professions (50+ professions across sectors):**
- Construction: Supervisors, Engineers, Laborers, Welders, Electricians, Plumbers
- IT: Software Developers, Network Engineers, Data Analysts, IT Support
- Healthcare: Doctors, Nurses, Pharmacists, Lab Technicians
- Hospitality: Hotel Managers, Chefs, Waiters, Housekeeping
- Transport: Heavy Truck Drivers, Bus Drivers, Logistics Coordinators
- Security: Security Guards, Supervisors
- Finance: Accountants, Financial Analysts, Auditors
- Education: Teachers, Professors, Trainers
- Retail: Sales Managers, Cashiers, Store Supervisors

**Generate realistic patterns:**
1. Each nationality has 3-6 "core" professions (Tier 1) based on historical patterns
2. Create dominance scenarios (e.g., Egypt 52% in Construction Supervisors)
3. Generate 12 months of historical requests with seasonal patterns
4. Create worker records with realistic visa expiry distribution
5. Generate some pending requests and queued items
6. Create establishments with varying utilization rates (20%-95%)

**Data Volume:**
- 500+ establishments
- 150,000+ worker records
- 5,000+ historical requests
- Current queue: 200-500 pending items

After generating:
```bash
git add .
git commit -m "feat: add database models and synthetic data generation"
git push origin main
```

Run tests to validate data integrity.

---

## PHASE 3: BUSINESS LOGIC ENGINES
**🎭 Act as: Senior Backend Engineer & Domain Expert in Quota Management Systems**

Build the core engines in `src/engines/`:

### 3.1 Tier Discovery Engine (`tier_discovery.py`)

```python
class TierDiscoveryEngine:
    """
    Discovers demand patterns per nationality from historical data.
    Runs monthly to classify professions into Tiers 1-4.
    """
    
    def discover_tiers(self, nationality_id: int, lookback_months: int = 12) -> List[NationalityTier]:
        """
        Tier 1 (Primary): >15% of requests
        Tier 2 (Secondary): 5-15% of requests  
        Tier 3 (Minor): 1-5% of requests
        Tier 4 (Unusual): <1% of requests
        
        Apply hysteresis (±2%) to prevent oscillation.
        Minimum sample size required for tier assignment.
        """
        pass
    
    def get_tier_for_request(self, nationality_id: int, profession_id: int) -> TierInfo:
        """Returns current tier classification for a nationality-profession pair."""
        pass
```

### 3.2 Capacity Engine (`capacity_engine.py`)

```python
class CapacityEngine:
    """
    Real-time calculation of headroom and tier availability.
    Core formula from spec Section 10.2.
    """
    
    def calculate_effective_headroom(self, nationality_id: int) -> HeadroomResult:
        """
        effective_headroom = cap - stock - committed - (pending × 0.8) + adjusted_outflow
        
        Where:
        - stock = COUNT(IN_COUNTRY workers)
        - committed = COUNT(COMMITTED - approved, not arrived)
        - pending = COUNT(PENDING requests) × 0.8 approval rate
        - adjusted_outflow = projected_final_exits × CONFIDENCE_FACTOR (0.75)
        """
        pass
    
    def calculate_tier_status(self, nationality_id: int) -> Dict[str, TierStatus]:
        """
        Returns status for each tier: OPEN, RATIONED, LIMITED, CLOSED
        
        Tier 1: OPEN if headroom >= tier1_demand, RATIONED if headroom > 0
        Tier 2: Opens only when headroom > tier1_projected_demand
        Tier 3: Opens only when headroom > tier1 + tier2 demand
        """
        pass
    
    def project_outflow(self, nationality_id: int, days: int = 30) -> OutflowProjection:
        """
        Outflow = FINAL EXITS ONLY (end of employment)
        NOT vacation travel, Ramadan visits, business trips
        
        Components:
        - FINAL_EXIT_VISAS scheduled
        - EXPIRING_CONTRACTS × NON_RENEWAL_RATIO
        """
        pass
```

### 3.3 Dominance Alert Engine (`dominance_engine.py`)

```python
class DominanceAlertEngine:
    """
    Monitors nationality concentration within professions.
    Additional check beyond tier allocation.
    """
    
    def check_dominance(self, nationality_id: int, profession_id: int) -> DominanceAlert:
        """
        Alert Levels (from spec Section 7):
        - CRITICAL: >50% share AND >10pp velocity → BLOCK
        - HIGH: 40-50% share AND >5pp velocity → PARTIAL only
        - WATCH: 30-40% share → FLAG for review
        - OK: <30% share → Normal processing
        
        MIN_PROFESSION_SIZE = 200 (dominance rules only apply above this)
        """
        pass
    
    def calculate_velocity(self, nationality_id: int, profession_id: int, years: int = 3) -> float:
        """Calculate share change over time (percentage points per period)."""
        pass
```

### 3.4 Request Processor (`request_processor.py`)

```python
class RequestProcessor:
    """
    Main decision engine - processes quota requests through all checks.
    """
    
    def process_request(self, request: QuotaRequest) -> Decision:
        """
        Decision Flow (from spec Section 6.1):
        1. Identify Tier for nationality-profession
        2. Check Tier Status (OPEN/RATIONED/LIMITED/CLOSED)
        3. If tier available, check Dominance Alert
        4. Calculate Priority Score
        5. Make decision: APPROVE / PARTIAL / QUEUE / BLOCK / REJECT
        
        Log everything to DecisionLog for audit.
        """
        pass
    
    def calculate_priority_score(self, request: QuotaRequest) -> int:
        """
        Priority Scoring (from spec Section 11.1):
        - HIGH_DEMAND_SKILL_FLAG: +50 points
        - Strategic Sector: +30 points
        - Utilization >90%: +20 points
        - Utilization 70-90%: +10 points
        - Utilization <30%: -20 points
        - Small Establishment: +10 points
        - Timestamp as tie-breaker
        """
        pass
```

### 3.5 Queue Processor (`queue_processor.py`)

```python
class QueueProcessor:
    """
    Manages the auto-queue: processes queued requests when capacity opens.
    """
    
    def add_to_queue(self, request: QuotaRequest) -> QueueEntry:
        """Add request to queue with position, expiry date (90 days)."""
        pass
    
    def process_queue_on_capacity_change(self, nationality_id: int) -> List[Decision]:
        """
        Triggered when tier status changes (outflow detected, cap adjusted).
        Process queue in priority order (Priority-Weighted FIFO).
        """
        pass
    
    def revalidate_queue(self, nationality_id: int) -> List[QueueEntry]:
        """
        Re-check eligibility on: tier open, dominance change, employer status change.
        Remove expired entries (>90 days).
        Send confirmation requests at day 30.
        """
        pass
```

### 3.6 AI Recommendation Engine (`ai_engine.py`)

**🎭 Act as: AI/ML Engineer specializing in Azure OpenAI Integration**

```python
class AIRecommendationEngine:
    """
    Uses Azure OpenAI to provide intelligent interpretations and recommendations.
    """
    
    def __init__(self):
        # Load Azure OpenAI credentials from .env
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    def generate_cap_recommendation(self, nationality_data: dict) -> str:
        """
        Given current stock, inflow/outflow trends, and demand patterns,
        generate AI-powered cap recommendations with rationale.
        """
        pass
    
    def explain_decision(self, decision_log: DecisionLog) -> str:
        """Generate human-readable explanation of why a request was approved/rejected."""
        pass
    
    def analyze_market_trends(self, nationality_id: int) -> str:
        """Analyze demand patterns and provide strategic insights."""
        pass
    
    def suggest_alternatives(self, rejected_request: QuotaRequest) -> str:
        """When request rejected, suggest alternative nationalities or timing."""
        pass
```

After building engines:
```bash
git add .
git commit -m "feat: implement core business logic engines (Tier, Capacity, Dominance, Queue, AI)"
git push origin main
```

Write unit tests for each engine in `tests/`.

---

## PHASE 4: API LAYER
**🎭 Act as: API Developer & REST Architecture Specialist**

Build FastAPI endpoints in `src/api/`:

```python
# Main endpoints needed:

# Dashboard Data
GET /api/v1/dashboard/{nationality_code}  # Live status for a nationality
GET /api/v1/dashboard/overview            # All nationalities summary

# Cap Management (Policymaker Interface)
GET /api/v1/caps                          # List all caps
GET /api/v1/caps/{nationality_id}/recommendation  # AI-powered cap recommendation
POST /api/v1/caps/{nationality_id}        # Set cap (requires auth)

# Tier Information
GET /api/v1/tiers/{nationality_code}      # Current tier classification
GET /api/v1/tiers/{nationality_code}/history  # Tier changes over time

# Request Processing
POST /api/v1/requests                     # Submit new quota request
GET /api/v1/requests/{request_id}         # Get request status
GET /api/v1/requests/{request_id}/explain # AI explanation of decision

# Queue Management
GET /api/v1/queue/{nationality_code}      # View queue for nationality
POST /api/v1/queue/{request_id}/withdraw  # Withdraw from queue

# Dominance Alerts
GET /api/v1/alerts/{nationality_code}     # Current dominance alerts
GET /api/v1/alerts/critical               # All critical alerts

# Reports & Analytics
GET /api/v1/reports/capacity-forecast     # Projected capacity over time
GET /api/v1/reports/dominance-trends      # Concentration trend analysis
```

After building API:
```bash
git add .
git commit -m "feat: implement REST API layer with all endpoints"
git push origin main
```

---

## PHASE 5: STREAMLIT FRONTEND
**🎭 Act as: Senior UX/UI Designer & Full-Stack Developer specializing in Data Dashboards**

Build a beautiful, professional Streamlit application in `app/`:

### Design Principles:
- **Clean, modern aesthetic** with consistent color scheme
- **Dark mode support** 
- **Responsive layout** that works on different screen sizes
- **Clear visual hierarchy** - most important info stands out
- **Professional Ministry branding** (Qatar colors: maroon, white, gold accents)

### App Structure:

```
app/
├── streamlit_app.py          # Main entry point with navigation
├── pages/
│   ├── 1_🏠_Dashboard.py     # Live monitoring dashboard
│   ├── 2_📊_Cap_Management.py # Policymaker cap setting
│   ├── 3_📝_Request_Portal.py # Submit/track requests
│   ├── 4_📈_Analytics.py      # Trends and insights
│   └── 5_⚙️_Settings.py       # Parameter configuration
└── components/
    ├── charts.py              # Reusable chart components
    ├── tables.py              # Styled tables
    ├── cards.py               # Status cards
    └── styles.py              # CSS and theming
```

### Page Designs:

#### 1. Dashboard (Main Page)
```
┌─────────────────────────────────────────────────────────────────────┐
│  🇶🇦 QATAR NATIONALITY QUOTA MANAGEMENT SYSTEM                      │
│  Ministry of Labour                              Last Updated: HH:MM │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [Nationality Selector Dropdown: Egypt ▼]                           │
│                                                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │   CAP       │ │   STOCK     │ │  HEADROOM   │ │   QUEUE     │   │
│  │  10,000     │ │   8,547     │ │    953      │ │    127      │   │
│  │             │ │  ████████░░ │ │   9.5%      │ │  requests   │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
│                                                                      │
│  TIER STATUS                           DOMINANCE ALERTS             │
│  ┌──────────────────────────┐         ┌──────────────────────────┐ │
│  │ Tier 1: ✅ OPEN          │         │ ⚠️ Construction Supv: 52%│ │
│  │ Tier 2: ⚠️ LIMITED (45)  │         │ ⚠️ Engineering: 48%     │ │
│  │ Tier 3: ❌ CLOSED        │         │ ✅ Heavy Drivers: 6%     │ │
│  │ Tier 4: ❌ CLOSED        │         └──────────────────────────┘ │
│  └──────────────────────────┘                                       │
│                                                                      │
│  CAPACITY PROJECTION (Next 90 Days)                                 │
│  [Line chart showing projected stock vs cap with confidence bands]  │
│                                                                      │
│  RECENT DECISIONS                                                   │
│  [Table: Request ID | Profession | Count | Decision | Date]         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 2. Cap Management (Policymaker View)
```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 CAP CONFIGURATION                                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [Select Nationality: Egypt ▼]                                      │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  CURRENT DATA                                                │   │
│  │  • Current Stock: 8,547                                      │   │
│  │  • Avg Monthly Inflow: 412                                   │   │
│  │  • Avg Monthly Outflow: 156                                  │   │
│  │  • Net Growth: +256/month                                    │   │
│  │  • Projected Year-End (no cap): 11,619                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  🤖 AI RECOMMENDATION                                        │   │
│  │  ──────────────────────────────────────────────────────────  │   │
│  │  Based on demand patterns and dominance alerts, I recommend: │   │
│  │                                                               │   │
│  │  Conservative: 9,500 ← Tight control                         │   │
│  │  ✓ Moderate: 10,000 ← Balanced (RECOMMENDED)                 │   │
│  │  Flexible: 11,000 ← Accommodates demand surge                │   │
│  │                                                               │   │
│  │  Rationale: Egyptian workers show strong demand in Tier 1    │   │
│  │  professions but dominance alerts in Construction suggest... │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  SET NEW CAP                                                        │
│  [Input: 10000] [Button: Confirm Cap]                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 3. Request Portal (Employer View)
```
┌─────────────────────────────────────────────────────────────────────┐
│  📝 QUOTA REQUEST PORTAL                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  NEW REQUEST                                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Establishment: [Dropdown]                                    │   │
│  │ Nationality: [Egypt ▼]                                       │   │
│  │ Profession: [Heavy Truck Driver ▼]                           │   │
│  │ Number of Workers: [20]                                      │   │
│  │                                                               │   │
│  │ ┌─ LIVE ELIGIBILITY CHECK ──────────────────────────────┐   │   │
│  │ │ Tier: 1 (Primary) ✅                                   │   │   │
│  │ │ Tier Status: OPEN ✅                                   │   │   │
│  │ │ Dominance: 6% - OK ✅                                  │   │   │
│  │ │ Establishment Utilization: 87% ✅                      │   │   │
│  │ │                                                         │   │   │
│  │ │ ✅ ELIGIBLE FOR IMMEDIATE APPROVAL                     │   │   │
│  │ └────────────────────────────────────────────────────────┘   │   │
│  │                                                               │   │
│  │ [Submit Request]                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  MY REQUESTS                                                        │
│  [Table with status tracking and AI explanations]                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4. Analytics Page
```
┌─────────────────────────────────────────────────────────────────────┐
│  📈 ANALYTICS & INSIGHTS                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [Tabs: Demand Patterns | Dominance Trends | Capacity Analysis]     │
│                                                                      │
│  DEMAND PATTERNS BY NATIONALITY                                     │
│  [Stacked bar chart showing Tier 1/2/3/4 distribution]              │
│                                                                      │
│  DOMINANCE EVOLUTION (3 Years)                                      │
│  [Multi-line chart showing share % over time per profession]        │
│                                                                      │
│  🤖 AI INSIGHTS                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Key observations for this period:                            │   │
│  │ • Egyptian share in Construction is accelerating (+4pp/yr)   │   │
│  │ • Indian IT professionals showing healthy diversification    │   │
│  │ • Nepal security guards approaching watch threshold (28%)    │   │
│  │                                                               │   │
│  │ Recommended actions:                                          │   │
│  │ • Consider reducing Egypt construction approvals by 15%      │   │
│  │ • Open Tier 2 for Philippines healthcare workers             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Styling (`components/styles.py`):

```python
# Color Scheme (Qatar-inspired)
COLORS = {
    'primary': '#8B1538',      # Qatar Maroon
    'secondary': '#1A365D',    # Deep Blue
    'accent': '#D4AF37',       # Gold
    'success': '#276749',      # Green
    'warning': '#C05621',      # Orange
    'danger': '#C53030',       # Red
    'background': '#F7FAFC',   # Light gray
    'card': '#FFFFFF',
    'text': '#2D3748',
    'muted': '#718096'
}

# Custom CSS for professional look
CUSTOM_CSS = """
<style>
    .main-header {
        background: linear-gradient(135deg, #8B1538 0%, #5D0E24 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #8B1538;
    }
    
    .status-open { color: #276749; font-weight: bold; }
    .status-limited { color: #C05621; font-weight: bold; }
    .status-closed { color: #C53030; font-weight: bold; }
    
    .ai-insight-box {
        background: linear-gradient(135deg, #EBF8FF 0%, #BEE3F8 100%);
        border-radius: 10px;
        padding: 1.5rem;
        border-left: 4px solid #2C5282;
    }
</style>
"""
```

After building frontend:
```bash
git add .
git commit -m "feat: implement beautiful Streamlit frontend with all pages"
git push origin main
```

---

## PHASE 6: INTEGRATION & TESTING
**🎭 Act as: QA Engineer & Integration Specialist**

1. **Integration Tests** (`tests/integration/`)
   - Test full request flow: submit → process → decision → queue
   - Test capacity recalculation when outflow occurs
   - Test queue auto-processing
   - Test AI recommendation generation

2. **Load Testing**
   - Simulate 100 concurrent requests
   - Verify data integrity under load

3. **Edge Cases**
   - What if cap is reached mid-request?
   - What if two requests for same nationality arrive simultaneously?
   - What if dominance changes while request in queue?

4. **End-to-End Scenarios**
   - Egyptian Tier 1 approval (normal flow)
   - Egyptian Tier 2 rejection → queue → auto-approval
   - Dominance block with alternatives suggested

```bash
git add .
git commit -m "test: add comprehensive integration and edge case tests"
git push origin main
```

---

## PHASE 7: DEPLOYMENT PREPARATION
**🎭 Act as: DevOps Engineer & Cloud Deployment Specialist**

1. **Streamlit Cloud Configuration**
   - Create `app/.streamlit/config.toml`
   - Configure secrets management
   - Set up environment variables

2. **Documentation**
   - Complete README with screenshots
   - API documentation
   - User guide for each role (Policymaker, Operator, Employer)

3. **Final Commits**
```bash
git add .
git commit -m "docs: add complete documentation and deployment config"
git push origin main
```

---

## EXECUTION INSTRUCTIONS

Please proceed phase by phase. After completing each phase:
1. Show me the code/output
2. Run any tests
3. Commit to GitHub with meaningful commit messages
4. Wait for my approval before proceeding to next phase

Start with **PHASE 0: PLANNING & ARCHITECTURE**.

Let me know when you've read and understood the technical specification document, then present your implementation plan.
```

---

## ADDITIONAL NOTES FOR CURSOR

### Azure OpenAI Configuration
The `.env` file should have:
```
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

### Key Business Rules to Implement
1. **Outflow = FINAL EXITS ONLY** (not vacation travel)
2. **Pipeline Commitments**: Must subtract COMMITTED and PENDING from headroom
3. **Confidence Factor**: Apply 0.75 to outflow projections
4. **Queue Expiry**: 90 days, with confirmation at day 30
5. **Dominance MIN_PROFESSION_SIZE**: 200 (don't apply to small professions)
6. **Tier Hysteresis**: ±2% to prevent oscillation

### What Success Looks Like
- Dashboard loads instantly with live data
- Can submit a request and see real-time eligibility check
- Can set caps and see AI recommendations
- Queue processes automatically when I manually add "outflow" events
- All decisions are logged with full explainability
- Beautiful, professional UI that looks like a real government system

