# Quota System - Calculation Formulas & Data Requirements

This document contains all formulas used in the Quota System with the exact data fields needed for each calculation.

---

## 1. Growth Rate Calculation

### Formula
```
Growth = (Total_2025 - Total_2024) / Total_2024 × 100
```

### Data Needed
| Field | Source | Description |
|-------|--------|-------------|
| `Total_2024` | Count from `07_worker_stock.csv` | Workers active during 2024 |
| `Total_2025` | Count from `07_worker_stock.csv` | Workers active during 2025 |

### Criteria for "Active in Year X"
A worker is **active in year X** if:
```
employment_start <= December 31 of Year X
AND
(employment_end IS NULL OR employment_end >= January 1 of Year X)
```

### Filter (Long-term only)
Only include workers where:
```
Employment_Duration >= 365 days

Where:
- If employment_end IS NULL: Duration = Today - employment_start
- If employment_end EXISTS: Duration = employment_end - employment_start
```

### Example (Yemen)
```
Total_2024 = Count of Yemen workers active in 2024 (long-term only)
Total_2025 = Count of Yemen workers active in 2025 (long-term only)
Growth = (Total_2025 - Total_2024) / Total_2024 × 100
```

---

## 2. Utilization Rate

### Formula
```
Utilization = (Current_Stock / Cap) × 100
```

### Data Needed
| Field | Source | Description |
|-------|--------|-------------|
| `Current_Stock` | `07_worker_stock.csv` | Workers with status = IN_COUNTRY (long-term only) |
| `Cap` | `05_nationality_caps.csv` | Field: `cap_limit` |

### For Outflow-Based Countries (EGY, SYR, YEM, IRN, IRQ)
```
Effective_Cap = Current_Stock (frozen at stock)
Utilization = 100%
```

---

## 3. Headroom (Available Capacity)

### Formula (Standard Countries)
```
Headroom = Cap - Stock - Committed - (Pending × 0.8) + (Projected_Outflow × 0.75)
```

### Simplified Formula (when Committed/Pending not available)
```
Headroom = Cap - Stock + (Projected_Outflow × 0.75)

Where:
Projected_Outflow = Stock × 0.015 × 3 (estimated 1.5% monthly outflow over 3 months)
```

### For Outflow-Based Countries
```
Headroom = 0 (no growth allowed)
```

### Data Needed
| Field | Source | Description |
|-------|--------|-------------|
| `Cap` | `05_nationality_caps.csv` | Field: `cap_limit` |
| `Stock` | `07_worker_stock.csv` | IN_COUNTRY workers (long-term only) |
| `Committed` | Request system | Approved but not arrived |
| `Pending` | Request system | Awaiting approval |

---

## 4. Dominance Share (Profession Concentration)

### Formula
```
Dominance_Share = Nationality_Workers_in_Profession / Total_Workers_in_Profession × 100
```

### Data Needed
| Field | Source | Description |
|-------|--------|-------------|
| `Nationality_Workers_in_Profession` | `07_worker_stock.csv` | Count of workers of nationality X in profession Y |
| `Total_Workers_in_Profession` | `07_worker_stock.csv` | Count of ALL workers (all nationalities) in profession Y |

### Filters
- Only professions with **Total >= 200 workers**
- Only **long-term workers** (employment >= 1 year)

### Alert Thresholds
| Level | Threshold |
|-------|-----------|
| WATCH | >= 30% |
| HIGH | >= 40% |
| CRITICAL | >= 50% |

### Example (Indian Diggers)
```
Indian_Diggers = 2,043
Total_Diggers = 2,855 (all nationalities)
Dominance = 2,043 / 2,855 × 100 = 71.6% → CRITICAL
```

---

## 5. Monthly Outflow

### Formula
```
Monthly_Outflow = (Left_2024 + Left_2025) / 23

Where:
- 23 = 12 months of 2024 + 11 months of 2025 (if data is through Nov 2025)
```

### Data Needed
| Field | Source | Description |
|-------|--------|-------------|
| `Left_2024` | `07_worker_stock.csv` | Workers where `employment_end` is in 2024 |
| `Left_2025` | `07_worker_stock.csv` | Workers where `employment_end` is in 2025 |

### Criteria for "Left in Year X"
```
employment_end >= January 1 of Year X
AND
employment_end <= December 31 of Year X
```

---

## 6. QVC Processing Capacity

### Formula
```
Monthly_Capacity = Daily_Capacity × 22 (working days)
Annual_Capacity = Daily_Capacity × 264 (working days)
```

### Data Needed
| Field | Source |
|-------|--------|
| `Daily_Capacity` | `qvc_capacity.json` |

---

## 7. Cap Recommendation Engine

### Decision Tree

```
IF country is Non-QVC AND growth < 0:
    IF country is in [EGY, SYR, YEM, IRN, IRQ]:
        Recommended_Cap = Current_Stock (FROZEN)
        Type = OUTFLOW-BASED
    ELSE (Afghanistan):
        Use standard recommendation
        Type = STANDARD

IF country is QVC OR Afghanistan:
    IF dominance_alerts >= 10:
        Recommended_Cap = Current_Cap × 1.05 (Conservative +5%)
    ELIF growth > 0:
        Recommended_Cap = Current_Cap × 1.10 (Moderate +10%)
    ELIF growth < -5%:
        Recommended_Cap = Current_Cap × 1.045 (Decline adjustment)
    ELSE:
        Recommended_Cap = Current_Cap × 1.08 (Standard +8%)
```

---

## 8. Current Stock Calculation

### Formula
```
Current_Stock = Count of workers WHERE:
    - nationality_code = [target nationality]
    - status = 'IN_COUNTRY'
    - employment_duration >= 365 days
```

### Employment Duration
```
IF employment_end IS NULL:
    Duration = Today - employment_start
ELSE:
    Duration = employment_end - employment_start
```

---

## Data Sources Summary

| File | Key Fields |
|------|------------|
| `07_worker_stock.csv` | `nationality_code`, `profession_code`, `status`, `employment_start`, `employment_end` |
| `05_nationality_caps.csv` | `nationality_code`, `cap_limit`, `previous_cap` |
| `01_nationalities.csv` | `nationality_code`, `nationality_name_en` |
| `02_professions.csv` | `profession_code`, `profession_name_en` |
| `qvc_capacity.json` | Daily processing capacity per country |

---

## Nationality Codes (12 Restricted)

| Country | ISO Code | Numeric Code | Type |
|---------|----------|--------------|------|
| India | IND | 356 | QVC |
| Bangladesh | BGD | 50 | QVC |
| Nepal | NPL | 524 | QVC |
| Pakistan | PAK | 586 | QVC |
| Philippines | PHL | 608 | QVC |
| Sri Lanka | LKA | 144 | QVC |
| Egypt | EGY | 818 | Non-QVC (Outflow) |
| Yemen | YEM | 886 | Non-QVC (Outflow) |
| Syria | SYR | 760 | Non-QVC (Outflow) |
| Iran | IRN | 364 | Non-QVC (Outflow) |
| Iraq | IRQ | 368 | Non-QVC (Outflow) |
| Afghanistan | AFG | 4 | Non-QVC (Standard) |

---

## Step-by-Step Manual Calculation

### For Each Nationality:

1. **Extract from `07_worker_stock.csv`:**
   - Filter by `nationality_code`
   - Apply long-term filter (duration >= 365 days)
   - Count `status = IN_COUNTRY` → **Current Stock**
   - Count active in 2024 → **Total_2024**
   - Count active in 2025 → **Total_2025**
   - Count by profession → **Profession Counts**

2. **Extract from `05_nationality_caps.csv`:**
   - Get `cap_limit` → **Cap**

3. **Calculate:**
   - **Growth** = (Total_2025 - Total_2024) / Total_2024 × 100
   - **Utilization** = Current_Stock / Cap × 100
   - **Headroom** = Cap - Current_Stock (simplified)

4. **For Dominance:**
   - For each profession with >= 200 total workers:
   - **Dominance** = Nationality_Count / Total_Count × 100
   - Flag if >= 30% (WATCH), >= 40% (HIGH), >= 50% (CRITICAL)

---

## Verification Checklist

- [ ] Growth rates match expected values
- [ ] Utilization never exceeds 100% for standard countries
- [ ] Outflow-based countries show 100% utilization
- [ ] Headroom is 0 for outflow-based countries
- [ ] Dominance alerts only for professions >= 200 workers
- [ ] All calculations exclude short-term workers (< 1 year)

---

*Document created: January 21, 2026*
