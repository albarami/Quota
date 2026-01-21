# Nationality Quota Allocation System
## Technical Documentation & User Guide

**Version:** 2.0  
**Document Date:** January 2026  
**Organization:** Qatar Ministry of Labour

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Core Principles](#2-core-principles)
3. [System Components](#3-system-components)
4. [Tier Classification System](#4-tier-classification-system)
5. [Capacity Engine](#5-capacity-engine)
6. [Dominance Alert System](#6-dominance-alert-system)
7. [Request Processing Flow](#7-request-processing-flow)
8. [Auto-Queue System](#8-auto-queue-system)
9. [Cap Recommendation Engine](#9-cap-recommendation-engine)
10. [QVC Processing Capacity](#10-qvc-processing-capacity)
11. [Formulas & Calculations](#11-formulas--calculations)
12. [Parameter Registry](#12-parameter-registry)

---

## 1. System Overview

### What is the Nationality Quota Allocation System?

The Nationality Quota Allocation System is a **dynamic, demand-driven quota management system** for Qatar's private sector labor market. It manages work permit allocations for restricted nationalities using intelligent automation while keeping policymakers in control of cap decisions.

### Purpose

The system addresses three key challenges:

1. **Managing Limited Quotas** - Each restricted nationality has an annual cap on work permits
2. **Prioritizing High-Demand Jobs** - Ensuring companies can hire for the most needed professions
3. **Preventing Concentration** - Avoiding over-dominance of any nationality in specific professions

### Key Innovation: Auto-Queue

When a tier is closed (no capacity), requests can be **queued and automatically processed** when capacity opens - triggered by workforce outflow, cap adjustments, or demand changes.

---

## 2. Core Principles

### Principle 1: Policy-Maker Controlled Caps

```
┌─────────────────────────────────────────────────────────────┐
│  POLICYMAKER ROLE                                           │
├─────────────────────────────────────────────────────────────┤
│  • Reviews historical data and demand patterns              │
│  • Receives AI-powered cap recommendations                  │
│  • Sets the final annual cap for each nationality           │
│  • System manages all allocation dynamically within cap     │
└─────────────────────────────────────────────────────────────┘
```

The system provides recommendations; **humans make final cap decisions**.

### Principle 2: Demand-Driven Tier Discovery

The system **automatically discovers** which professions are in high demand for each nationality by analyzing historical request patterns. Professions are classified into tiers based on their share of total workforce.

### Principle 3: Dynamic Capacity Protection

```
HIGH DEMAND (Tier 1) → Protected First → Always gets priority
     ↓
When Tier 1 satisfied → Tier 2 opens
     ↓
When Tier 1+2 satisfied → Tier 3 opens
     ↓
When all above satisfied → Tier 4 opens
```

---

## 3. System Components

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  Dashboard  │ │ Cap Manager │ │Request Portal│               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Tier Discovery  │  │ Capacity Engine │  │ Dominance Alert │ │
│  │     Engine      │  │                 │  │     Engine      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │    Request      │  │     Queue       │  │       AI        │ │
│  │   Processor     │  │   Processor     │  │  Recommendation │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Nationalities │ Professions │ Workers │ Requests │ Caps │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

| Component | Purpose | Key Functions |
|-----------|---------|---------------|
| **Tier Discovery Engine** | Identifies demand patterns | Classifies professions into Tiers 1-4 based on share |
| **Capacity Engine** | Calculates available headroom | Real-time cap utilization and projections |
| **Dominance Alert Engine** | Monitors concentration risk | Triggers alerts when thresholds exceeded |
| **Request Processor** | Processes quota applications | Makes approve/reject/queue decisions |
| **Queue Processor** | Manages waiting requests | Auto-processes when capacity opens |
| **AI Recommendation Engine** | Provides intelligent insights | Cap recommendations and decision explanations |

---

## 4. Tier Classification System

### Purpose

The tier system identifies **demand patterns** for each nationality. Since quotas are limited, tiers determine **allocation priority**:

- **Tier 1 jobs get served FIRST**
- **Lower tiers open only when higher tiers are satisfied**

### Tier Definitions

| Tier | Name | Share Range | Description | Allocation Priority |
|------|------|-------------|-------------|---------------------|
| **Tier 1** | Primary | > 15% | Highest demand professions | **HIGHEST** - Served first |
| **Tier 2** | Secondary | 5% - 15% | High demand professions | HIGH - Opens when Tier 1 satisfied |
| **Tier 3** | Minor | 1% - 5% | Moderate demand | MEDIUM - Opens when Tier 1+2 satisfied |
| **Tier 4** | Unusual | < 1% | Low demand / specialized | LOW - Opens when capacity available |

### Tier Calculation Formula

```
Share Percentage = (Workers in Profession / Total Workers of Nationality) × 100

IF Share >= 15%    → Tier 1 (Primary)
IF Share >= 5%     → Tier 2 (Secondary)
IF Share >= 1%     → Tier 3 (Minor)
IF Share < 1%      → Tier 4 (Unusual)
```

### Hysteresis (Prevents Oscillation)

To prevent professions from constantly switching tiers at boundary values:

```
TIER_HYSTERESIS = 2%

Example: A profession at 14.5% stays in Tier 2
         Only moves to Tier 1 when it reaches 15% + 2% = 17%
         Only drops from Tier 1 when it falls to 15% - 2% = 13%
```

### Tier Status Determination

```
IF effective_headroom >= tier_demand THEN status = "OPEN"
IF effective_headroom > 0 BUT < tier_demand THEN status = "RATIONED"
IF effective_headroom <= 0 THEN status = "CLOSED"
```

For lower tiers:
```
tier2_surplus = headroom - tier1_projected_demand
tier2_status = "OPEN" if tier2_surplus >= tier2_demand else "LIMITED" if tier2_surplus > 0 else "CLOSED"

tier3_surplus = tier2_surplus - tier2_projected_demand
tier3_status = calculated similarly...
```

---

## 5. Capacity Engine

### Purpose

Calculates **real-time headroom** (available capacity) for each nationality, accounting for:
- Current workers (stock)
- Committed workers (approved but not arrived)
- Pending requests (likely to be approved)
- Projected outflows (workers leaving)

### Effective Headroom Formula

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  EFFECTIVE HEADROOM = Cap - Stock - Committed - (Pending × 0.8)   │
│                       + (Projected_Outflow × 0.75)                 │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

Where:
- **Cap** = Annual nationality cap set by policymakers
- **Stock** = COUNT(workers with state = IN_COUNTRY)
- **Committed** = COUNT(workers approved but not yet arrived)
- **Pending** = COUNT(requests under review) × 0.8 (approval rate)
- **Projected_Outflow** = Expected departures × 0.75 (confidence factor)

### Outflow Projection Formula

**IMPORTANT:** Outflow = FINAL EXITS ONLY (not vacation travel, Ramadan visits, or business trips)

```
Projected_Outflow = Scheduled_Final_Exits + (Expiring_Contracts × Non_Renewal_Ratio)

Adjusted_Outflow = Projected_Outflow × CONFIDENCE_FACTOR (0.75)
```

### Utilization Calculation

```
Utilization % = (Current_Stock / Cap) × 100

Example:
  Stock = 400,273
  Cap = 487,741
  Utilization = (400,273 / 487,741) × 100 = 82.1%
```

---

## 6. Dominance Alert System

### Purpose

**SEPARATE from Tier Classification** - The dominance system monitors concentration risk to prevent any single nationality from dominating specific professions in the labor market.

### Alert Thresholds

| Alert Level | Share Threshold | Velocity Threshold | Action Required |
|-------------|-----------------|-------------------|-----------------|
| **OK** | < 30% | Any | Normal processing |
| **WATCH** | 30% - 39% | Any | Flag for review, monitor trends |
| **HIGH** | 40% - 49% | > 5pp/3yr | Partial approvals only |
| **CRITICAL** | ≥ 50% | > 10pp/3yr | **Block new approvals** |

### Dominance Share Formula

```
Dominance_Share = (Nationality_Workers_in_Profession / Total_Workers_in_Profession) × 100

Example:
  Pakistani Drivers = 64,632
  Total Drivers (all nationalities) = 196,500
  Dominance Share = (64,632 / 196,500) × 100 = 32.9%
  → WATCH ALERT triggered
```

### Velocity Calculation

Measures how fast a nationality is increasing its share in a profession:

```
Velocity = (Current_Share - Share_3_Years_Ago) / 3

Example:
  Current Share = 32.9%
  3 Years Ago = 25.0%
  Velocity = (32.9 - 25.0) / 3 = 2.6 percentage points per year
```

### Minimum Profession Size Rule

Dominance rules **only apply** to professions with sufficient workers:

```
MIN_PROFESSION_SIZE = 200

IF total_workers_in_profession < 200:
    dominance_check = SKIP (profession too small for meaningful analysis)
```

---

## 7. Request Processing Flow

### Decision Flow Diagram

```
                    ┌─────────────────┐
                    │  New Request    │
                    │  Submitted      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ 1. Identify     │
                    │    Tier Level   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
              ┌─────│ 2. Check Tier   │─────┐
              │     │    Status       │     │
              │     └─────────────────┘     │
              │                             │
         OPEN/RATIONED                   CLOSED
              │                             │
              ▼                             ▼
     ┌─────────────────┐           ┌─────────────────┐
     │ 3. Check        │           │ Offer to Queue  │
     │    Dominance    │           │ (Auto-Process   │
     └────────┬────────┘           │  when opens)    │
              │                    └─────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
   OK              ALERT (>30%)
    │                   │
    ▼                   ▼
┌─────────┐      ┌─────────────┐
│ 4. Calc │      │ Partial or  │
│ Priority│      │ Block       │
│ Score   │      └─────────────┘
└────┬────┘
     │
     ▼
┌─────────────────┐
│ 5. DECISION     │
│ APPROVE/PARTIAL │
└─────────────────┘
```

### Decision Outcomes

| Decision | Condition | Action |
|----------|-----------|--------|
| **APPROVE** | Tier open, no dominance alert | Full request approved |
| **PARTIAL** | Tier rationed OR dominance HIGH | Reduced count approved |
| **QUEUE** | Tier closed, no dominance block | Added to auto-queue |
| **BLOCK** | Dominance CRITICAL (>50%) | Rejected, alternatives suggested |
| **REJECT** | Invalid request or policy violation | Rejected with reason |

---

## 8. Auto-Queue System

### How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                      AUTO-QUEUE LIFECYCLE                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Day 0: Request submitted → Tier CLOSED → Added to Queue         │
│         Position assigned based on priority score                │
│                                                                  │
│  Day 1-29: Waiting in queue                                      │
│            System monitors for capacity changes                  │
│                                                                  │
│  Day 30: Confirmation request sent to applicant                  │
│          "Do you still want this allocation?"                    │
│                                                                  │
│  Day 31-89: Continue waiting if confirmed                        │
│                                                                  │
│  Day 90: Queue entry EXPIRES if not processed                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Queue Processing Triggers

The queue automatically processes when:

1. **Outflow Detected** - Workers leave, creating headroom
2. **Cap Adjusted** - Policymaker increases the cap
3. **Tier Status Changes** - Lower tier opens up
4. **Dominance Alert Cleared** - Concentration drops below threshold

### Priority-Weighted FIFO

Queue is processed in priority order (not pure first-come-first-served):

```
Queue_Position = f(Priority_Score, Submission_Timestamp)

Higher priority scores get processed first
Timestamp breaks ties
```

---

## 9. Cap Recommendation Engine

### Recommendation Models

The AI engine provides three cap options:

| Model | Formula | Use Case |
|-------|---------|----------|
| **Conservative** | Current_Cap × 1.05 | High risk, many alerts |
| **Moderate** | Current_Cap × 1.10 | Balanced growth |
| **Flexible** | Current_Cap × 1.20 | Low risk, high demand |

### Selection Logic

```
IF dominance_alerts > 3 OR has_critical_alert:
    recommendation = CONSERVATIVE
    
ELIF utilization > 90% OR dominance_alerts > 1:
    recommendation = MODERATE
    
ELIF utilization < 80% AND dominance_alerts == 0:
    recommendation = FLEXIBLE
    
ELSE:
    recommendation = MODERATE
```

### Growth Adjustment

```
IF growth_rate > 5%:
    recommended_cap = recommended_cap × 1.05  # Accommodate growth
    
IF growth_rate < -5%:
    recommended_cap = recommended_cap × 0.95  # Reduce for decline
```

---

## 10. QVC Processing Capacity

### What is QVC?

**QVC (Qatar Visa Center)** is the final processing step after ministry approval. Workers must visit a QVC office in their home country to complete visa processing before traveling to Qatar.

**IMPORTANT:** QVC capacity is **per country** - each country's QVC center(s) can only process workers from that specific nationality.

### Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        VISA APPROVAL TO ENTRY FLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: Ministry Approval                                                  │
│          ↓                                                                  │
│  Step 2: Approved request added to QVC Processing Queue                     │
│          ↓                                                                  │
│  Step 3: QVC processes up to DAILY_CAPACITY per day                        │
│          ↓                                                                  │
│  Step 4: Worker completes QVC → Visa issued → Travel to Qatar              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### QVC Centers and Capacity (Per Country)

| # | Country | Centers | Locations | Daily Capacity |
|---|---------|--------:|-----------|---------------:|
| 1 | Sri Lanka | 1 | Colombo (150) | **150** |
| 2 | Bangladesh | 2 | Dhaka (425), Sylhet (90) | **515** |
| 3 | Pakistan | 2 | Islamabad (300), Karachi (70) | **370** |
| 4 | India | 7 | Delhi (120), Mumbai (120), Chennai (150), Kolkata (65), Hyderabad (100), Lucknow (100), Kochi (150) | **805** |
| 5 | Nepal | 1 | Kathmandu (325) | **325** |
| 6 | Philippines | 1 | Manila (280) | **280** |

**Note:** Only QVC countries are listed. Non-QVC countries (Egypt, Yemen, Syria, Iraq, Afghanistan, Iran) do not have QVC centers - their visa processing follows different procedures.

### QVC Utilization Formula

```python
# Daily QVC utilization for a nationality
qvc_pending = COUNT(approved_requests with status = PENDING_QVC)
qvc_daily_capacity = QVC_CAPACITY[nationality_code]

# Days to clear current backlog
qvc_backlog_days = qvc_pending / qvc_daily_capacity

# QVC utilization percentage
qvc_utilization = min(100, (daily_approved_requests / qvc_daily_capacity) * 100)
```

### Why QVC Capacity Matters

1. **Bottleneck Identification** - Even if ministry approves many requests, QVC capacity limits actual throughput
2. **Processing Time Estimation** - Helps estimate how long until approved workers can enter Qatar
3. **Approval Pacing** - Avoid overwhelming QVC by pacing approvals appropriately
4. **Resource Planning** - Identify when QVC capacity expansion may be needed

### QVC Backlog Alert Thresholds

| Backlog Days | Alert Level | Action |
|--------------|-------------|--------|
| < 7 days | **OK** | Normal processing |
| 7-14 days | **WATCH** | Monitor, consider pacing approvals |
| 14-30 days | **HIGH** | Slow down new approvals for this nationality |
| > 30 days | **CRITICAL** | Pause new approvals until backlog clears |

### QVC Monthly Capacity Calculation

```python
# Working days per month (assuming 22 working days)
WORKING_DAYS_PER_MONTH = 22

# Monthly capacity per country
qvc_monthly_capacity = qvc_daily_capacity * WORKING_DAYS_PER_MONTH

# Example: Bangladesh
# Daily: 515 × 22 = 11,330 workers/month maximum throughput
```

### QVC Countries Summary

| Country | Daily | Monthly (22 days) | Share of Total |
|---------|------:|------------------:|---------------:|
| India | 805 | 17,710 | 32.9% |
| Bangladesh | 515 | 11,330 | 21.1% |
| Pakistan | 370 | 8,140 | 15.1% |
| Nepal | 325 | 7,150 | 13.3% |
| Philippines | 280 | 6,160 | 11.4% |
| Sri Lanka | 150 | 3,300 | 6.1% |
| **TOTAL** | **2,445** | **53,790** | 100% |

---

## 10.B Non-QVC Countries: Outflow-Based Allocation

### What are Non-QVC Countries?

Five nationalities do **NOT** have QVC centers and follow a different visa processing procedure:
- **Egypt (EGY)**
- **Yemen (YEM)**
- **Syria (SYR)**
- **Iraq (IRQ)**
- **Iran (IRN)**

### The Outflow-Based Allocation Model

For non-QVC countries with **negative growth** (more workers leaving than arriving), the monthly allocation capacity is determined by the **previous month's outflow**. This creates a **replacement model** - new workers can only be brought in to replace those who left.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   OUTFLOW-BASED MONTHLY CAPACITY                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: Count workers who LEFT in previous month (final exits only)        │
│          ↓                                                                  │
│  Step 2: That count becomes THIS month's available capacity                 │
│          ↓                                                                  │
│  Step 3: Approve new requests up to that capacity                          │
│          ↓                                                                  │
│  Step 4: Repeat monthly - rolling allocation based on actual outflow       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Monthly Capacity Formula

```python
# For non-QVC countries with negative growth
monthly_capacity = COUNT(workers with final_exit_date in previous_month)

# Example: Egypt in February 2026
# January 2026 exits: 723 workers left (final exit)
# February 2026 capacity: 723 new approvals allowed
```

### Why Outflow-Based Allocation?

1. **Natural Replacement** - Maintains stable workforce levels without growth
2. **Cap Protection** - Prevents exceeding the annual nationality cap
3. **Predictable Flow** - Monthly capacity is based on actual data, not estimates
4. **Shrinking Management** - For declining nationalities, ensures controlled reduction

### Non-QVC Countries Data (Current)

| Country | Stock | Cap | Utilization | Growth Rate | Est. Monthly Outflow |
|---------|------:|----:|------------:|------------:|---------------------:|
| Egypt | 71,574 | 81,668 | 87.6% | -10.79% | ~725 |
| Syria | 23,324 | 27,038 | 86.3% | -12.37% | ~284 |
| Yemen | 13,105 | 14,949 | 87.7% | -1.26% | ~14 |
| Iraq | 1,658 | 1,959 | 84.6% | -6.38% | ~9 |
| Iran | 6,683 | 7,768 | 86.0% | -6.79% | ~41 |

*Est. Monthly Outflow = (Stock × |Growth Rate|) / 12*

### Calculation Details

```python
# Monthly outflow estimation from annual growth rate
annual_outflow = current_stock * abs(growth_rate) / 100
monthly_outflow = annual_outflow / 12

# Example: Egypt
# Stock: 71,574
# Growth: -10.79%
# Annual outflow: 71,574 × 10.79% = 7,723 workers/year
# Monthly outflow: 7,723 / 12 = 644 workers/month (approx)

# Actual from data: Left_2025 = 8,703 total
# Monthly average: 8,703 / 12 = 725 workers/month
```

### Key Difference: QVC vs Non-QVC

| Aspect | QVC Countries | Non-QVC Countries |
|--------|---------------|-------------------|
| **Capacity Source** | QVC center daily limit | Previous month's outflow |
| **Capacity Type** | Fixed daily maximum | Variable monthly based on exits |
| **Growth Trend** | Can be positive or negative | Typically negative (shrinking) |
| **Bottleneck** | QVC processing speed | Replacement slots available |
| **Planning** | Predictable (fixed capacity) | Variable (depends on outflow) |

---

## 11. Formulas & Calculations

### Complete Formula Reference

#### A. Tier Classification
```python
share_pct = workers_in_profession / total_nationality_workers

tier = 1 if share_pct >= 0.15 else \
       2 if share_pct >= 0.05 else \
       3 if share_pct >= 0.01 else 4
```

#### B. Effective Headroom
```python
effective_headroom = cap \
                   - stock \
                   - committed \
                   - (pending * PENDING_APPROVAL_RATE) \
                   + (projected_outflow * CONFIDENCE_FACTOR)

# Default values:
PENDING_APPROVAL_RATE = 0.8
CONFIDENCE_FACTOR = 0.75
```

#### C. Utilization
```python
utilization = (current_stock / cap) * 100
```

#### D. Dominance Share
```python
dominance_share = nationality_workers_in_prof / total_workers_in_prof * 100
```

#### E. Dominance Velocity
```python
velocity = (current_share - share_3_years_ago) / 3  # pp per year
```

#### F. Priority Score
```python
priority_score = 0

# Skill demand
if profession.high_demand_flag:
    priority_score += 50

# Strategic sector
if establishment.sector in ['Healthcare', 'IT', 'Education']:
    priority_score += 30

# Establishment utilization
if establishment.utilization > 0.90:
    priority_score += 20
elif establishment.utilization > 0.70:
    priority_score += 10
elif establishment.utilization < 0.30:
    priority_score -= 20

# Small business support
if establishment.total_workers < 50:
    priority_score += 10

# Timestamp as tiebreaker (earlier = higher)
```

#### G. Growth Rate
```python
net_change = recent_entries - recent_exits  # 6-month period
growth_rate = net_change / current_stock * 100
```

#### H. Projected Stock
```python
projected_annual_growth = current_stock * growth_rate * 2  # Annualized
projected_stock = current_stock + projected_annual_growth
```

---

## 12. Parameter Registry

### Configurable Thresholds

All thresholds are configurable through the Parameter Registry:

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| **TIER_1_THRESHOLD** | 15% | 10-20% | Primary profession threshold |
| **TIER_2_THRESHOLD** | 5% | 3-8% | Secondary profession threshold |
| **TIER_3_THRESHOLD** | 1% | 0.5-2% | Minor profession threshold |
| **TIER_HYSTERESIS** | 2% | 1-3% | Prevents tier oscillation |
| **MIN_REQUESTS_FOR_TIER** | 50 | 20-100 | Minimum sample for tier assignment |

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| **DOMINANCE_CRITICAL** | 50% | 45-55% | Block new approvals |
| **DOMINANCE_HIGH** | 40% | 35-50% | Partial approve only |
| **DOMINANCE_WATCH** | 30% | 25-40% | Flag for review |
| **VELOCITY_CRITICAL** | 10pp/3yr | 8-15pp | Accelerating dominance trigger |
| **MIN_PROFESSION_SIZE** | 200 | 100-500 | Dominance rules minimum |

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| **PROJECTION_HORIZON_DAYS** | 180 | 90-180 | Forecast window |
| **OUTFLOW_CONFIDENCE_FACTOR** | 0.75 | 0.6-0.9 | Conservative buffer |
| **PENDING_APPROVAL_RATE** | 0.8 | 0.7-0.9 | Expected approval rate |
| **QUEUE_EXPIRY_DAYS** | 90 | 60-120 | Queue entry lifetime |
| **QUEUE_CONFIRM_DAYS** | 30 | 20-45 | Confirmation request timing |
| **RECALC_FREQUENCY_MINS** | 15 | 5-60 | Status recalculation interval |

---

## Summary

### System Benefits

1. **Fair Allocation** - High-demand jobs get priority, ensuring market needs are met
2. **Risk Management** - Dominance alerts prevent unhealthy concentration
3. **Automation** - Auto-queue reduces manual processing
4. **Transparency** - All decisions logged with full audit trail
5. **Flexibility** - Policymakers retain control over caps
6. **Intelligence** - AI provides data-driven recommendations

### Key Distinction

| Concept | Purpose | Threshold | Action |
|---------|---------|-----------|--------|
| **Tier System** | Prioritize allocation | >15%, >5%, >1% | Determines processing order |
| **Dominance Alert** | Monitor concentration | >30%, >40%, >50% | Triggers intervention |

**Tiers = Demand Priority**  
**Dominance = Risk Control**

---

*Document Version: 2.0*  
*Last Updated: January 2026*
