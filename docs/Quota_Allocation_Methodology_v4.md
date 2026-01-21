# Nationality Quota Allocation System
## Calculation Methodology & Technical Documentation

**Document Version:** 4.0  
**Date:** January 2026  
**Organization:** Qatar Ministry of Labour  
**Classification:** Technical Reference

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Fundamental Principles](#2-fundamental-principles)
3. [Data Requirements](#3-data-requirements)
4. [Country Classification](#4-country-classification)
5. [Core Calculations](#5-core-calculations)
6. [QVC Capacity Constraint](#6-qvc-capacity-constraint)
7. [Cap Recommendation Framework](#7-cap-recommendation-framework)
8. [Tier Classification System](#8-tier-classification-system)
9. [Dominance Alert System](#9-dominance-alert-system)
10. [Monitoring Metrics](#10-monitoring-metrics)
11. [Worked Examples](#11-worked-examples)
12. [Implementation Reference](#12-implementation-reference)
13. [Appendices](#13-appendices)

---

## 1. Executive Summary

### 1.1 Purpose

This document defines the calculation methodology for Qatar's Nationality Quota Allocation System. The system determines recommended annual caps for restricted nationalities in Qatar's private sector workforce based on:

- Current workforce stock
- Actual demand patterns (joiners)
- Historical outflow patterns
- Qatar Visa Center (QVC) processing capacity
- Growth trends

### 1.2 Key Innovation

The methodology recognizes **three binding constraints**:

| Constraint | Description | Impact |
|------------|-------------|--------|
| **Stock** | Current workers in country | Base population to maintain |
| **Demand** | Workers joining annually (actual growth) | Capacity requirement |
| **QVC Capacity** | Maximum annual visa processing | Hard ceiling on inflow |

**Critical Insight:** 
1. A recommended cap must reflect **actual demand** (joiners), not just replacement (outflow)
2. A recommended cap that exceeds QVC processing capacity is operationally meaningless

### 1.3 The Core Formula

```
For Positive Growth:  Cap = Stock + Joiners + Buffer
For Negative Growth:  Cap = Stock + Outflow + Buffer (or frozen)

Both subject to:      Cap ≤ Stock + Net_QVC_Capacity
```

### 1.4 Scope

This methodology applies to 12 restricted nationalities:

**QVC Countries (6):** Bangladesh, India, Nepal, Pakistan, Philippines, Sri Lanka

**Non-QVC Countries (6):** Egypt, Yemen, Syria, Iraq, Iran, Afghanistan

---

## 2. Fundamental Principles

### 2.1 Principle 1: Demand-Driven Caps

Caps must reflect **actual demand** as measured by historical joiners, not just replacement capacity.

```
Actual_Demand = Average_Annual_Joiners (workers who entered employment)
Replacement_Need = Average_Annual_Outflow (workers who left employment)
Net_Growth = Joiners - Outflow
```

- **Positive Growth (Joiners > Outflow):** Use Joiners as the demand basis
- **Negative Growth (Joiners < Outflow):** Use Outflow as replacement capacity

### 2.2 Principle 2: Physical Constraints Take Precedence

No policy cap can override physical processing limitations.

```
Effective_Cap = min(Demand_Based_Cap, QVC_Constrained_Cap)
```

### 2.3 Principle 3: Buffer for Operational Flexibility

A buffer is added to handle demand fluctuations:

| Growth Direction | Buffer | Rationale |
|------------------|--------|-----------|
| Positive Growth | 10% of Stock | Room for demand surges |
| Negative Growth (QVC) | 5% of Stock | Conservative; demand declining |
| Negative Growth (Non-QVC) | 0% | Frozen at stock; replacement only |

### 2.4 Principle 4: Differentiated Treatment

Countries are treated differently based on:
- Whether they have QVC centers (processing constraint)
- Whether their workforce is growing or declining (demand direction)

---

## 3. Data Requirements

### 3.1 Required Data Files

| File | Contents | Key Fields |
|------|----------|------------|
| `worker_stock.csv` | All worker records | nationality_code, profession_code, status, employment_start, employment_end |
| `nationalities.csv` | Nationality reference | code, name, is_restricted |
| `professions.csv` | Profession reference | code, name |
| `nationality_caps.csv` | Current cap limits | nationality_code, year, cap_limit |
| `qvc_capacity.json` | QVC processing limits | country_code, daily_capacity |

### 3.2 Data Filtering Rules

**Critical:** All calculations exclude short-term workers.

```python
# Include only long-term workers (1+ year employment)
valid_workers = workers WHERE employment_duration >= 365 days

# Employment duration calculation
IF employment_end IS NULL:
    duration = TODAY - employment_start
ELSE:
    duration = employment_end - employment_start
```

### 3.3 Worker Status Definitions

| Status | Definition | Included in Stock? |
|--------|------------|:------------------:|
| `IN_COUNTRY` | Active visa, physically present | ✅ Yes |
| `COMMITTED` | Approved, visa issued, not arrived | ❌ No |
| `PENDING` | Application under review | ❌ No |
| `LEFT` | Employment ended, exited country | ❌ No |

---

## 4. Country Classification

### 4.1 Classification Framework

```
                    ┌─────────────────────────────────────┐
                    │        RESTRICTED NATIONALITIES      │
                    │              (12 Total)              │
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    │                                      │
           ┌────────▼────────┐                  ┌─────────▼─────────┐
           │  QVC COUNTRIES  │                  │  NON-QVC COUNTRIES │
           │   (6 Countries) │                  │    (6 Countries)   │
           └────────┬────────┘                  └─────────┬─────────┘
                    │                                      │
    ┌───────────────┼───────────────┐          ┌──────────┴──────────┐
    │               │               │          │                      │
 POSITIVE       NEGATIVE            │    ┌─────▼─────┐        ┌──────▼──────┐
 GROWTH         GROWTH              │    │ OUTFLOW   │        │  STANDARD   │
    │               │               │    │  BASED    │        │ TREATMENT   │
    ▼               ▼               │    │(5 Countries)│       │(1 Country)  │
 Joiners +      Outflow +           │    └───────────┘        └─────────────┘
 10% Buffer     5% Buffer           │          │                     │
                                    │    • Egypt (EGY)         • Afghanistan
    Subject to QVC Constraint       │    • Yemen (YEM)           (AFG)
                                    │    • Syria (SYR)
                                    │    • Iraq (IRQ)
                                    │    • Iran (IRN)
                                    │
                                    │    Cap = Stock (Frozen)
                                    │    Monthly allocation = Outflow/12
```

### 4.2 QVC Countries

**Definition:** Countries with Qatar Visa Center offices where workers must complete visa processing before traveling to Qatar.

**Constraint:** Annual inflow cannot exceed QVC processing capacity.

**Treatment:** 
- Positive growth → Cap based on Joiners + 10% buffer
- Negative growth → Cap based on Outflow + 5% buffer
- Both subject to QVC constraint

**Countries:**
| Country | Code | QVC Locations |
|---------|------|---------------|
| Bangladesh | BGD | Dhaka, Sylhet |
| India | IND | Delhi, Mumbai, Chennai, Kolkata, Hyderabad, Lucknow, Kochi |
| Nepal | NPL | Kathmandu |
| Pakistan | PAK | Islamabad, Karachi |
| Philippines | PHL | Manila |
| Sri Lanka | LKA | Colombo |

### 4.3 Non-QVC Outflow-Based Countries

**Definition:** Countries without QVC centers that have negative workforce growth.

**Constraint:** Cap frozen at current stock. Only replacement of departing workers allowed.

**Treatment:** 
- Cap = Current Stock (frozen)
- Monthly Allocation = Average Monthly Outflow
- Headroom = 0
- Utilization = 100%

**Countries:** Egypt, Yemen, Syria, Iraq, Iran

### 4.4 Non-QVC Standard Countries

**Definition:** Countries without QVC centers with positive or neutral growth.

**Treatment:**
- Positive growth → Cap based on Joiners + 5% buffer
- Negative growth → Cap based on Outflow + 5% buffer

**Countries:** Afghanistan

---

## 5. Core Calculations

### 5.1 Current Stock

**Definition:** Number of workers currently employed and present in Qatar.

```python
Current_Stock = COUNT(workers) WHERE:
    status = 'IN_COUNTRY'
    AND employment_duration >= 365 days
    AND nationality_code = [target]
```

### 5.2 Average Annual Joiners

**Definition:** Average number of new workers entering employment per year.

```python
Joined_2024 = COUNT(workers) WHERE employment_start IN year 2024
Joined_2025 = COUNT(workers) WHERE employment_start IN year 2025

Avg_Annual_Joiners = (Joined_2024 + Joined_2025) / 2
```

**This represents ACTUAL DEMAND** — how many workers the market absorbed.

### 5.3 Average Annual Outflow

**Definition:** Average number of workers leaving employment per year.

```python
Left_2024 = COUNT(workers) WHERE employment_end IN year 2024
Left_2025 = COUNT(workers) WHERE employment_end IN year 2025

Avg_Annual_Outflow = (Left_2024 + Left_2025) / 2
```

**Important:** Outflow = FINAL EXITS ONLY
- ✅ Employment contract ended
- ✅ Final exit visa processed
- ❌ NOT vacation travel
- ❌ NOT Ramadan visits
- ❌ NOT business trips

### 5.4 Growth Determination

**Definition:** Whether workforce is expanding or contracting.

```python
Net_Growth = Avg_Annual_Joiners - Avg_Annual_Outflow

IF Net_Growth > 0:
    growth_direction = "POSITIVE"  # Workforce expanding
ELSE:
    growth_direction = "NEGATIVE"  # Workforce contracting or stable
```

### 5.5 Growth Rate

**Definition:** Percentage change in workforce year-over-year.

```python
Total_2024 = COUNT(workers active during 2024)
Total_2025 = COUNT(workers active during 2025)

Growth_Rate = ((Total_2025 - Total_2024) / Total_2024) × 100
```

### 5.6 Utilization

**Definition:** Percentage of cap currently in use.

```python
Utilization = (Current_Stock / Recommended_Cap) × 100
```

### 5.7 Headroom

**Definition:** Available capacity for new workers.

```python
Headroom = Recommended_Cap - Current_Stock
```

---

## 6. QVC Capacity Constraint

### 6.1 QVC Capacity Data

| Country | Daily Capacity | Monthly (×22 days) | Annual (×264 days) |
|---------|---------------:|-------------------:|-------------------:|
| Sri Lanka | 150 | 3,300 | 39,600 |
| Bangladesh | 515 | 11,330 | 135,960 |
| Pakistan | 370 | 8,140 | 97,680 |
| India | 805 | 17,710 | 212,520 |
| Nepal | 325 | 7,150 | 85,800 |
| Philippines | 280 | 6,160 | 73,920 |
| **TOTAL** | **2,445** | **53,790** | **645,480** |

### 6.2 The Constraint Logic

To maintain or grow workforce at a given cap level:

```
Required_Annual_Inflow = Annual_Outflow + (Cap - Stock)
```

This inflow **cannot exceed** QVC annual capacity:

```
Annual_Outflow + (Cap - Stock) ≤ QVC_Annual_Capacity
```

Solving for maximum achievable cap:

```
Cap ≤ Stock + QVC_Annual_Capacity - Annual_Outflow
Cap ≤ Stock + Net_QVC_Capacity
```

### 6.3 Net QVC Capacity

**Definition:** QVC capacity remaining after replacement needs are met.

```python
Net_QVC_Capacity = QVC_Annual_Capacity - Avg_Annual_Outflow
```

**Interpretation:**

| Net QVC Value | Meaning | Implication |
|---------------|---------|-------------|
| **Positive** | QVC can handle replacement AND growth | Workforce can expand |
| **Zero** | QVC exactly matches replacement need | Workforce can maintain but not grow |
| **Negative** | QVC cannot keep up with outflow | Workforce WILL shrink regardless of cap |

### 6.4 Maximum Achievable Cap

```python
Maximum_Achievable_Cap = Current_Stock + Net_QVC_Capacity
```

This is the **hard ceiling** — no policy decision can exceed this without expanding QVC capacity.

---

## 7. Cap Recommendation Framework

### 7.1 The Complete Formula

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FOR POSITIVE GROWTH (Joiners > Outflow):                                  │
│                                                                             │
│      Desired_Cap = Stock + Avg_Annual_Joiners + (Stock × Buffer%)          │
│                                                                             │
│  FOR NEGATIVE GROWTH (Joiners ≤ Outflow):                                  │
│                                                                             │
│      Desired_Cap = Stock + Avg_Annual_Outflow + (Stock × Buffer%)          │
│                                                                             │
│  THEN APPLY QVC CONSTRAINT (for QVC countries):                            │
│                                                                             │
│      Recommended_Cap = min(Desired_Cap, Stock + Net_QVC_Capacity)          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Why Joiners for Positive Growth?

| Metric | What It Measures | When to Use |
|--------|------------------|-------------|
| **Joiners** | Actual demand (workers market absorbed) | Positive growth |
| **Outflow** | Replacement need (workers who left) | Negative growth |

**Example:**
```
Stock = 100,000
Joiners = 25,000/year
Outflow = 15,000/year
Net Growth = +10,000/year (POSITIVE)

WRONG:  Cap = 100,000 + 15,000 + 10% = 125,000  (ignores growth demand)
RIGHT:  Cap = 100,000 + 25,000 + 10% = 135,000  (captures actual demand)
```

Using Joiners ensures the cap accommodates:
- Replacement of workers who leave (Outflow portion)
- Additional workers for growth (Net Growth portion)

### 7.3 Decision Tree

```
START
  │
  ├─── Is nationality a QVC country? (BGD, IND, NPL, PAK, PHL, LKA)
  │         │
  │         YES
  │         │
  │         ├─── Step 1: Determine Growth Direction
  │         │    IF Joiners > Outflow → POSITIVE GROWTH
  │         │    ELSE → NEGATIVE GROWTH
  │         │
  │         ├─── Step 2: Calculate Desired Cap
  │         │    IF POSITIVE: Desired = Stock + Joiners + (Stock × 10%)
  │         │    IF NEGATIVE: Desired = Stock + Outflow + (Stock × 5%)
  │         │
  │         ├─── Step 3: Calculate QVC Constraint
  │         │    Net_QVC = QVC_Annual - Outflow
  │         │    Max_Achievable = Stock + Net_QVC
  │         │
  │         ├─── Step 4: Apply Constraint
  │         │    Recommended = min(Desired, Max_Achievable)
  │         │
  │         └─── Step 5: Flag if Constrained
  │              IF Desired > Max_Achievable → "QVC Constrained"
  │
  └─── Is nationality NON-QVC?
            │
            ├─── Is it EGY, YEM, SYR, IRN, or IRQ?
            │         │
            │         YES (Outflow-Based)
            │         │
            │         └─── Cap = Current_Stock (FROZEN)
            │              Monthly_Allocation = Outflow / 12
            │              Headroom = 0
            │              Utilization = 100%
            │
            └─── Is it AFG?
                      │
                      YES (Standard Non-QVC)
                      │
                      ├─── Determine Growth Direction
                      │    IF Joiners > Outflow → POSITIVE
                      │    ELSE → NEGATIVE
                      │
                      └─── Calculate Cap
                           IF POSITIVE: Cap = Stock + Joiners + (Stock × 5%)
                           IF NEGATIVE: Cap = Stock + Outflow + (Stock × 5%)
```

### 7.4 Formula Summary Table

| Country Type | Growth | Formula | Buffer |
|--------------|--------|---------|--------|
| **QVC** | Positive | min(Stock + Joiners + 10%, Stock + Net_QVC) | 10% |
| **QVC** | Negative | min(Stock + Outflow + 5%, Stock + Net_QVC) | 5% |
| **Non-QVC Outflow** | N/A | Stock (frozen) | 0% |
| **Non-QVC Standard** | Positive | Stock + Joiners + 5% | 5% |
| **Non-QVC Standard** | Negative | Stock + Outflow + 5% | 5% |

### 7.5 Complete Algorithm

```python
# =============================================================================
# CONSTANTS
# =============================================================================
QVC_COUNTRIES = ['BGD', 'IND', 'NPL', 'PAK', 'PHL', 'LKA']
OUTFLOW_BASED = ['EGY', 'YEM', 'SYR', 'IRN', 'IRQ']
STANDARD_NON_QVC = ['AFG']

QVC_ANNUAL_CAPACITY = {
    'BGD': 135960,   # 515 × 264
    'IND': 212520,   # 805 × 264
    'NPL': 85800,    # 325 × 264
    'PAK': 97680,    # 370 × 264
    'PHL': 73920,    # 280 × 264
    'LKA': 39600     # 150 × 264
}

BUFFER_POSITIVE_QVC = 0.10      # 10% for positive growth QVC
BUFFER_NEGATIVE_QVC = 0.05      # 5% for negative growth QVC
BUFFER_STANDARD_NON_QVC = 0.05  # 5% for standard non-QVC
BUFFER_OUTFLOW_BASED = 0.00     # 0% for outflow-based (frozen)

# =============================================================================
# MAIN CALCULATION FUNCTION
# =============================================================================
def calculate_recommended_cap(nationality_code, stock, avg_joiners, avg_outflow):
    """
    Calculate recommended cap for a nationality.
    
    Args:
        nationality_code: ISO 3-letter country code
        stock: Current workers in country (long-term only)
        avg_joiners: Average workers joining per year
        avg_outflow: Average workers leaving per year
    
    Returns:
        Dictionary with cap recommendation and supporting metrics
    """
    
    # Determine growth direction
    is_positive_growth = avg_joiners > avg_outflow
    net_growth = avg_joiners - avg_outflow
    
    # =========================================================================
    # QVC COUNTRIES
    # =========================================================================
    if nationality_code in QVC_COUNTRIES:
        qvc_annual = QVC_ANNUAL_CAPACITY[nationality_code]
        
        # Calculate Net QVC capacity
        net_qvc = qvc_annual - avg_outflow
        
        # Maximum achievable cap (QVC constraint)
        max_achievable = stock + net_qvc
        
        # Calculate desired cap based on growth direction
        if is_positive_growth:
            # Use JOINERS for positive growth (captures actual demand)
            demand = avg_joiners
            buffer = stock * BUFFER_POSITIVE_QVC
        else:
            # Use OUTFLOW for negative growth (replacement capacity)
            demand = avg_outflow
            buffer = stock * BUFFER_NEGATIVE_QVC
        
        desired_cap = stock + demand + buffer
        
        # Apply QVC constraint
        recommended_cap = min(desired_cap, max_achievable)
        
        # Determine if constrained
        is_constrained = desired_cap > max_achievable
        
        # Calculate metrics
        headroom = recommended_cap - stock
        utilization = (stock / recommended_cap) * 100 if recommended_cap > 0 else 100
        
        return {
            'nationality_code': nationality_code,
            'type': 'QVC',
            'growth_direction': 'POSITIVE' if is_positive_growth else 'NEGATIVE',
            'current_stock': stock,
            'avg_annual_joiners': avg_joiners,
            'avg_annual_outflow': avg_outflow,
            'net_growth': net_growth,
            'demand_basis': 'Joiners' if is_positive_growth else 'Outflow',
            'demand_value': demand,
            'buffer_pct': BUFFER_POSITIVE_QVC if is_positive_growth else BUFFER_NEGATIVE_QVC,
            'buffer_value': buffer,
            'qvc_annual_capacity': qvc_annual,
            'net_qvc_capacity': net_qvc,
            'max_achievable_cap': max_achievable,
            'desired_cap': desired_cap,
            'recommended_cap': recommended_cap,
            'is_qvc_constrained': is_constrained,
            'headroom': headroom,
            'utilization': round(utilization, 1)
        }
    
    # =========================================================================
    # NON-QVC OUTFLOW-BASED (Frozen)
    # =========================================================================
    elif nationality_code in OUTFLOW_BASED:
        monthly_allocation = avg_outflow / 12
        
        return {
            'nationality_code': nationality_code,
            'type': 'OUTFLOW_BASED',
            'growth_direction': 'FROZEN',
            'current_stock': stock,
            'avg_annual_joiners': avg_joiners,
            'avg_annual_outflow': avg_outflow,
            'recommended_cap': stock,
            'monthly_allocation': round(monthly_allocation),
            'headroom': 0,
            'utilization': 100.0
        }
    
    # =========================================================================
    # NON-QVC STANDARD
    # =========================================================================
    elif nationality_code in STANDARD_NON_QVC:
        # Calculate cap based on growth direction
        if is_positive_growth:
            demand = avg_joiners
        else:
            demand = avg_outflow
        
        buffer = stock * BUFFER_STANDARD_NON_QVC
        recommended_cap = stock + demand + buffer
        
        headroom = demand + buffer
        utilization = (stock / recommended_cap) * 100 if recommended_cap > 0 else 100
        
        return {
            'nationality_code': nationality_code,
            'type': 'STANDARD_NON_QVC',
            'growth_direction': 'POSITIVE' if is_positive_growth else 'NEGATIVE',
            'current_stock': stock,
            'avg_annual_joiners': avg_joiners,
            'avg_annual_outflow': avg_outflow,
            'net_growth': net_growth,
            'demand_basis': 'Joiners' if is_positive_growth else 'Outflow',
            'demand_value': demand,
            'buffer_pct': BUFFER_STANDARD_NON_QVC,
            'buffer_value': buffer,
            'recommended_cap': recommended_cap,
            'headroom': headroom,
            'utilization': round(utilization, 1)
        }
    
    else:
        raise ValueError(f"Unknown nationality code: {nationality_code}")
```

---

## 8. Tier Classification System

### 8.1 Purpose

The tier system identifies **demand patterns within each nationality**. It determines which professions get allocation priority when capacity is limited.

### 8.2 Tier Definitions

| Tier | Name | Share Threshold | Priority | Description |
|------|------|-----------------|----------|-------------|
| **Tier 1** | Primary | ≥ 15% | HIGHEST | Dominant professions, served first |
| **Tier 2** | Secondary | ≥ 5% and < 15% | HIGH | Significant professions |
| **Tier 3** | Minor | ≥ 1% and < 5% | MEDIUM | Moderate presence |
| **Tier 4** | Unusual | < 1% | LOW | Specialized/niche |

### 8.3 Tier Share Formula

```python
Tier_Share = (Workers_in_Profession / Total_Workers_of_Nationality) × 100
```

**Key Distinction:**
- **Tier Share:** Profession as % of nationality (within nationality)
- **Dominance Share:** Nationality as % of profession (across all nationalities)

### 8.4 Classification Algorithm

```python
def classify_tier(share_percentage):
    """
    Classify profession into tier based on share percentage.
    """
    if share_percentage >= 15.0:
        return 1  # Primary
    elif share_percentage >= 5.0:
        return 2  # Secondary
    elif share_percentage >= 1.0:
        return 3  # Minor
    else:
        return 4  # Unusual
```

### 8.5 Tier Hysteresis

To prevent professions from oscillating between tiers at boundary values:

```python
HYSTERESIS = 2.0  # percentage points

# Moving UP a tier requires exceeding threshold + hysteresis
# Moving DOWN a tier requires falling below threshold - hysteresis

Example:
- Profession at 14.5% stays in Tier 2
- Only moves to Tier 1 when it reaches 17% (15% + 2%)
- Only drops from Tier 1 when it falls to 13% (15% - 2%)
```

---

## 9. Dominance Alert System

### 9.1 Purpose

**Separate from Tier Classification** — The dominance system monitors concentration risk to prevent any single nationality from dominating specific professions across the entire labor market.

### 9.2 Dominance Share Formula

```python
Dominance_Share = (Nationality_Workers_in_Profession / Total_Workers_in_Profession) × 100
```

### 9.3 Alert Thresholds

| Alert Level | Share Threshold | Action Required |
|-------------|-----------------|-----------------|
| **OK** | < 30% | Normal processing |
| **WATCH** | ≥ 30% and < 40% | Monitor trends, flag for review |
| **HIGH** | ≥ 40% and < 50% | Partial approvals only |
| **CRITICAL** | ≥ 50% | Block new approvals |

### 9.4 Minimum Profession Size

Dominance rules **only apply** to professions with sufficient total workers:

```python
MIN_PROFESSION_SIZE = 200

def check_dominance(nationality_workers, total_profession_workers):
    if total_profession_workers < MIN_PROFESSION_SIZE:
        return None  # Skip small professions
    
    dominance_share = (nationality_workers / total_profession_workers) * 100
    
    if dominance_share >= 50:
        return 'CRITICAL'
    elif dominance_share >= 40:
        return 'HIGH'
    elif dominance_share >= 30:
        return 'WATCH'
    else:
        return 'OK'
```

---

## 10. Monitoring Metrics

### 10.1 QVC Health Metrics

| Metric | Formula | Warning | Critical |
|--------|---------|---------|----------|
| **QVC Utilization** | `(Outflow / QVC_Annual) × 100` | > 80% | > 95% |
| **Net QVC Capacity** | `QVC_Annual - Outflow` | < 20,000 | < 5,000 |
| **Replacement Ratio** | `Outflow / QVC_Annual` | > 0.80 | > 0.95 |

### 10.2 Cap Health Metrics

| Metric | Formula | Warning | Critical |
|--------|---------|---------|----------|
| **Cap Utilization** | `(Stock / Cap) × 100` | > 90% | > 98% |
| **Headroom** | `Cap - Stock` | < 10% of Cap | < 2% of Cap |
| **Years to Reach Cap** | `Headroom / Net_Growth` | > 3 years | > 5 years |

### 10.3 Alert Triggers

| Alert Type | Trigger | Action |
|------------|---------|--------|
| **QVC Saturation** | Net_QVC < 0 | Flag: "QVC cannot maintain workforce" |
| **Near Saturation** | Replacement Ratio > 0.90 | Flag: "Approaching QVC limit" |
| **Dominance Critical** | Any profession ≥ 50% | Block new approvals for that profession |
| **Cap Exhaustion** | Utilization > 98% | Freeze new approvals |

---

## 11. Worked Examples

### 11.1 Example: India (QVC Country, Negative Growth)

**Input Data:**
```
Current Stock:        488,672
Joined 2024:          145,000
Joined 2025:          98,000
Left 2024:            157,395
Left 2025:            109,767
QVC Daily Capacity:   805
```

**Step 1: Calculate Averages**
```
Avg_Annual_Joiners = (145,000 + 98,000) / 2 = 121,500
Avg_Annual_Outflow = (157,395 + 109,767) / 2 = 133,581
```

**Step 2: Determine Growth Direction**
```
Net_Growth = 121,500 - 133,581 = -12,081
Growth Direction = NEGATIVE (Joiners < Outflow)
```

**Step 3: Calculate Desired Cap (using Outflow for negative growth)**
```
Demand_Basis = Outflow = 133,581
Buffer = 488,672 × 5% = 24,434
Desired_Cap = 488,672 + 133,581 + 24,434 = 646,687
```

**Step 4: Calculate QVC Constraint**
```
QVC_Annual = 805 × 264 = 212,520
Net_QVC = 212,520 - 133,581 = 78,939
Max_Achievable = 488,672 + 78,939 = 567,611
```

**Step 5: Apply Constraint**
```
Recommended_Cap = min(646,687, 567,611) = 567,611
Is_Constrained = YES (646,687 > 567,611)
```

**Step 6: Calculate Metrics**
```
Headroom = 567,611 - 488,672 = 78,939
Utilization = (488,672 / 567,611) × 100 = 86.1%
```

**Result:**
| Metric | Value |
|--------|-------|
| Growth Direction | Negative |
| Demand Basis | Outflow (133,581) |
| Buffer | 5% (24,434) |
| Desired Cap | 646,687 |
| QVC Constraint | 567,611 |
| **Recommended Cap** | **567,611** |
| QVC Constrained | Yes |
| Headroom | 78,939 |
| Utilization | 86.1% |

---

### 11.2 Example: Philippines (QVC Country, Positive Growth)

**Input Data:**
```
Current Stock:        120,269
Joined 2024:          35,000
Joined 2025:          32,000
Left 2024:            26,000
Left 2025:            30,868
QVC Daily Capacity:   280
```

**Step 1: Calculate Averages**
```
Avg_Annual_Joiners = (35,000 + 32,000) / 2 = 33,500
Avg_Annual_Outflow = (26,000 + 30,868) / 2 = 28,434
```

**Step 2: Determine Growth Direction**
```
Net_Growth = 33,500 - 28,434 = +5,066
Growth Direction = POSITIVE (Joiners > Outflow)
```

**Step 3: Calculate Desired Cap (using Joiners for positive growth)**
```
Demand_Basis = Joiners = 33,500
Buffer = 120,269 × 10% = 12,027
Desired_Cap = 120,269 + 33,500 + 12,027 = 165,796
```

**Step 4: Calculate QVC Constraint**
```
QVC_Annual = 280 × 264 = 73,920
Net_QVC = 73,920 - 28,434 = 45,486
Max_Achievable = 120,269 + 45,486 = 165,755
```

**Step 5: Apply Constraint**
```
Recommended_Cap = min(165,796, 165,755) = 165,755
Is_Constrained = YES (barely: 165,796 > 165,755)
```

**Result:**
| Metric | Value |
|--------|-------|
| Growth Direction | Positive |
| Demand Basis | Joiners (33,500) |
| Buffer | 10% (12,027) |
| Desired Cap | 165,796 |
| QVC Constraint | 165,755 |
| **Recommended Cap** | **165,755** |
| QVC Constrained | Yes (barely) |
| Headroom | 45,486 |

---

### 11.3 Example: Egypt (Non-QVC Outflow-Based)

**Input Data:**
```
Current Stock:        71,536
Left 2024:            9,903
Left 2025:            8,699
Growth Rate:          -5.5% (negative)
```

**Step 1: Confirm Outflow-Based Treatment**
```
Egypt is non-QVC AND in OUTFLOW_BASED list → Cap frozen at stock
```

**Step 2: Calculate Cap**
```
Recommended_Cap = Current_Stock = 71,536
```

**Step 3: Calculate Monthly Allocation**
```
Avg_Annual_Outflow = (9,903 + 8,699) / 2 = 9,301
Monthly_Allocation = 9,301 / 12 = 775 workers/month
```

**Result:**
| Metric | Value |
|--------|-------|
| Treatment | Outflow-Based (Frozen) |
| **Recommended Cap** | **71,536** |
| Monthly Allocation | 775 |
| Headroom | 0 |
| Utilization | 100% |

---

### 11.4 Example: Afghanistan (Non-QVC Standard, Positive Growth)

**Input Data:**
```
Current Stock:        2,532
Joined 2024:          300
Joined 2025:          280
Left 2024:            134
Left 2025:            126
```

**Step 1: Calculate Averages**
```
Avg_Annual_Joiners = (300 + 280) / 2 = 290
Avg_Annual_Outflow = (134 + 126) / 2 = 130
```

**Step 2: Determine Growth Direction**
```
Net_Growth = 290 - 130 = +160
Growth Direction = POSITIVE
```

**Step 3: Calculate Recommended Cap (using Joiners)**
```
Demand_Basis = Joiners = 290
Buffer = 2,532 × 5% = 127
Recommended_Cap = 2,532 + 290 + 127 = 2,949
```

**Step 4: Calculate Metrics**
```
Headroom = 2,949 - 2,532 = 417
Utilization = (2,532 / 2,949) × 100 = 85.9%
```

**Result:**
| Metric | Value |
|--------|-------|
| Growth Direction | Positive |
| Demand Basis | Joiners (290) |
| Buffer | 5% (127) |
| **Recommended Cap** | **2,949** |
| Headroom | 417 |
| Utilization | 85.9% |

---

## 12. Implementation Reference

### 12.1 Code Constants

```python
# Country Classifications
QVC_COUNTRIES = ['BGD', 'IND', 'NPL', 'PAK', 'PHL', 'LKA']
OUTFLOW_BASED = ['EGY', 'YEM', 'SYR', 'IRN', 'IRQ']
STANDARD_NON_QVC = ['AFG']

# QVC Capacity (annual, based on 264 working days)
QVC_ANNUAL_CAPACITY = {
    'LKA': 39600,   # 150 × 264
    'BGD': 135960,  # 515 × 264
    'PAK': 97680,   # 370 × 264
    'IND': 212520,  # 805 × 264
    'NPL': 85800,   # 325 × 264
    'PHL': 73920    # 280 × 264
}

# Buffer Percentages
BUFFER_POSITIVE_QVC = 0.10      # 10% for positive growth QVC
BUFFER_NEGATIVE_QVC = 0.05      # 5% for negative growth QVC
BUFFER_STANDARD_NON_QVC = 0.05  # 5% for standard non-QVC

# Tier Thresholds
TIER_1_THRESHOLD = 15.0     # Primary
TIER_2_THRESHOLD = 5.0      # Secondary
TIER_3_THRESHOLD = 1.0      # Minor
TIER_HYSTERESIS = 2.0       # Prevent oscillation

# Dominance Thresholds
DOMINANCE_CRITICAL = 50.0
DOMINANCE_HIGH = 40.0
DOMINANCE_WATCH = 30.0
MIN_PROFESSION_SIZE = 200

# Working Days
WORKING_DAYS_PER_MONTH = 22
WORKING_DAYS_PER_YEAR = 264
```

### 12.2 SQL Queries Reference

**Current Stock:**
```sql
SELECT nationality_code, COUNT(*) as stock
FROM worker_stock
WHERE status = 'IN_COUNTRY'
  AND DATEDIFF(COALESCE(employment_end, CURRENT_DATE), employment_start) >= 365
GROUP BY nationality_code;
```

**Annual Joiners:**
```sql
SELECT 
    nationality_code,
    SUM(CASE WHEN YEAR(employment_start) = 2024 THEN 1 ELSE 0 END) as joined_2024,
    SUM(CASE WHEN YEAR(employment_start) = 2025 THEN 1 ELSE 0 END) as joined_2025
FROM worker_stock
WHERE DATEDIFF(COALESCE(employment_end, CURRENT_DATE), employment_start) >= 365
GROUP BY nationality_code;
```

**Annual Outflow:**
```sql
SELECT 
    nationality_code,
    SUM(CASE WHEN YEAR(employment_end) = 2024 THEN 1 ELSE 0 END) as left_2024,
    SUM(CASE WHEN YEAR(employment_end) = 2025 THEN 1 ELSE 0 END) as left_2025
FROM worker_stock
WHERE employment_end IS NOT NULL
  AND DATEDIFF(employment_end, employment_start) >= 365
GROUP BY nationality_code;
```

**Tier Classification:**
```sql
SELECT 
    w.nationality_code,
    w.profession_code,
    COUNT(*) as profession_count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY w.nationality_code) as tier_share
FROM worker_stock w
WHERE w.status = 'IN_COUNTRY'
  AND DATEDIFF(COALESCE(w.employment_end, CURRENT_DATE), w.employment_start) >= 365
GROUP BY w.nationality_code, w.profession_code;
```

**Dominance Check:**
```sql
SELECT 
    w.profession_code,
    w.nationality_code,
    COUNT(*) as nationality_count,
    SUM(COUNT(*)) OVER (PARTITION BY w.profession_code) as total_profession,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY w.profession_code) as dominance_share
FROM worker_stock w
WHERE w.status = 'IN_COUNTRY'
  AND DATEDIFF(COALESCE(w.employment_end, CURRENT_DATE), w.employment_start) >= 365
GROUP BY w.profession_code, w.nationality_code
HAVING SUM(COUNT(*)) OVER (PARTITION BY w.profession_code) >= 200;
```

---

## 13. Appendices

### Appendix A: Formula Quick Reference

| Scenario | Formula |
|----------|---------|
| **QVC + Positive Growth** | `min(Stock + Joiners + 10%, Stock + Net_QVC)` |
| **QVC + Negative Growth** | `min(Stock + Outflow + 5%, Stock + Net_QVC)` |
| **Non-QVC Outflow-Based** | `Stock` (frozen) |
| **Non-QVC Standard + Positive** | `Stock + Joiners + 5%` |
| **Non-QVC Standard + Negative** | `Stock + Outflow + 5%` |

### Appendix B: QVC Capacity by Location

| Country | City | Daily Capacity |
|---------|------|---------------:|
| **Bangladesh** | Dhaka | 425 |
| | Sylhet | 90 |
| | **Subtotal** | **515** |
| **India** | Delhi | 120 |
| | Mumbai | 120 |
| | Chennai | 150 |
| | Kolkata | 65 |
| | Hyderabad | 100 |
| | Lucknow | 100 |
| | Kochi | 150 |
| | **Subtotal** | **805** |
| **Nepal** | Kathmandu | 325 |
| **Pakistan** | Islamabad | 300 |
| | Karachi | 70 |
| | **Subtotal** | **370** |
| **Philippines** | Manila | 280 |
| **Sri Lanka** | Colombo | 150 |
| **GRAND TOTAL** | | **2,445** |

### Appendix C: Glossary

| Term | Definition |
|------|------------|
| **Cap** | Maximum permitted workers of a nationality |
| **Headroom** | Available capacity (Cap - Stock) |
| **Joiners** | Workers who entered employment (actual demand) |
| **Net Growth** | Joiners - Outflow |
| **Net QVC** | QVC capacity remaining after replacement needs |
| **Outflow** | Workers leaving employment (final exits only) |
| **QVC** | Qatar Visa Center |
| **Stock** | Current workers in country |
| **Tier** | Profession priority classification within nationality |
| **Dominance** | Nationality concentration within a profession |
| **Utilization** | Percentage of cap currently used |

### Appendix D: Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 2026 | Initial framework |
| 2.0 | Jan 2026 | Added tier and dominance systems |
| 3.0 | Jan 2026 | Added QVC capacity constraint |
| 4.0 | Jan 2026 | Corrected formula to use Joiners for positive growth |

---

## Document Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Prepared By | | | |
| Reviewed By | | | |
| Approved By | | | |

---

**End of Document**

*Qatar Ministry of Labour - Nationality Quota Allocation System*  
*Calculation Methodology & Technical Documentation v4.0*
