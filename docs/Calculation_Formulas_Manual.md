# Quota System - Calculation Formulas & Data Requirements

This document contains all formulas used in the Quota System with explanations for each metric.

---

## 1. Growth Rate

### What is it?
**Growth Rate** measures how the workforce of a nationality has changed year-over-year. A positive growth means more workers are entering than leaving. A negative growth means more workers are leaving than entering.

### Why is it important?
- Helps predict future workforce trends
- Determines whether a nationality needs more recruitment capacity or is naturally declining
- Used to decide if a country should use "outflow-based allocation" (frozen cap)

### Formula
```
Growth = (Total_2025 - Total_2024) / Total_2024 × 100
```

### What data do you need?
| Data | How to get it |
|------|---------------|
| **Total_2024** | Count all workers of that nationality who were employed at any point during 2024 |
| **Total_2025** | Count all workers of that nationality who were employed at any point during 2025 |

### How to count "Active in Year X"
A worker was **active in 2024** if:
- Their `employment_start` date is on or before December 31, 2024
- AND their `employment_end` date is either empty (still working) OR on or after January 1, 2024

### Important Filter
Only count **long-term workers** (employment duration >= 365 days). Short-term workers are excluded from all calculations.

### Example
```
Yemen Total 2024 = 14,080
Yemen Total 2025 = 13,301
Growth = (13,301 - 14,080) / 14,080 × 100 = -5.5%
```
This means Yemen's workforce declined by 5.5% from 2024 to 2025.

---

## 2. Current Stock

### What is it?
**Current Stock** is the number of workers from a specific nationality who are currently present and working in the country.

### Why is it important?
- Shows how many workers are actually in the country right now
- Used as the BASE for calculating recommended caps
- For outflow-based countries, this becomes the cap itself

### Formula
```
Current_Stock = Count of workers WHERE:
    - nationality_code = [target nationality]
    - status = 'IN_COUNTRY'
    - employment_duration >= 365 days (long-term only)
```

### What data do you need?
| Data | How to get it |
|------|---------------|
| **Workers with status IN_COUNTRY** | Filter `07_worker_stock.csv` by `status = 'IN_COUNTRY'` |
| **Employment duration** | Calculate from `employment_start` to `employment_end` (or today if still employed) |

---

## 3. Utilization Rate

### What is it?
**Utilization** shows what percentage of the recommended cap is currently being used. It answers: "How full is the quota?"

### Why is it important?
- Shows if there's room for more workers or if the quota is nearly full
- Helps identify nationalities that might need cap adjustments
- A utilization of 100% means no new workers can be added

### Formula
```
Utilization = (Current_Stock / Recommended_Cap) × 100
```

### Special Rule for Outflow-Based Countries
For Egypt, Syria, Yemen, Iran, and Iraq:
```
Recommended_Cap = Current_Stock (frozen at stock level)
Utilization = 100% (always full, no growth allowed)
```

### Example
```
India Stock = 488,672
India Recommended Cap = 590,000
Utilization = 488,672 / 590,000 × 100 = 82.8%
```

---

## 4. Headroom (Available Capacity)

### What is it?
**Headroom** is the number of additional workers that can be added before reaching the cap. It represents available capacity for new hires.

### Why is it important?
- Shows how many new workers can be approved
- Helps plan recruitment and visa processing
- A headroom of 0 means no new workers can be added

### Formula
```
Headroom = Recommended_Cap - Current_Stock
```

### Special Rule for Outflow-Based Countries
```
Headroom = 0 (no growth allowed)
```
These countries can only replace workers who leave, not add new ones.

### Example
```
India Recommended Cap = 590,000
India Stock = 488,672
Headroom = 590,000 - 488,672 = 101,328
```

---

## 5. Recommended Cap Calculation (NEW - Data-Driven)

### What is it?
The **Recommended Cap** is the suggested maximum number of workers for each nationality. This is calculated from actual data - there are NO pre-existing caps.

### Why is it important?
- Sets the limit for how many workers of each nationality can be employed
- Balances demand with workforce management goals
- Controls growth for nationalities with concentration risk

---

### Formula for Countries with POSITIVE GROWTH:

```
Recommended_Cap = Current_Stock + Projected_Demand + Operational_Buffer
```

**Where:**
```
Projected_Demand = (Joined_2024 + Joined_2025) / 2
Operational_Buffer = Current_Stock × 0.15 (15% headroom)
```

**Full Formula:**
```
Recommended_Cap = Stock + Avg_Annual_Joiners + (Stock × 0.15)
```

**Example (if Bangladesh had positive growth):**
```
Stock = 330,602
Joined_2024 = 66,697
Joined_2025 = 2,086
Avg_Annual_Joiners = (66,697 + 2,086) / 2 = 34,392
Operational_Buffer = 330,602 × 0.15 = 49,590

Recommended_Cap = 330,602 + 34,392 + 49,590 = 414,584
```

---

### Formula for Countries with NEGATIVE GROWTH (QVC Countries):

```
Recommended_Cap = Current_Stock + (Current_Stock × 0.05)
```

**Rationale:** Minimal 5% buffer for operational flexibility, but no significant growth expected.

**Example (India - negative growth):**
```
Stock = 488,672
Recommended_Cap = 488,672 + (488,672 × 0.05) = 513,106
```

---

### Formula for Countries with NEGATIVE GROWTH (Non-QVC, Outflow-Based):

For Egypt, Syria, Yemen, Iran, Iraq:

```
Recommended_Cap = Current_Stock (FROZEN)
Monthly_Allocation = Average_Monthly_Outflow
```

**Where:**
```
Average_Monthly_Outflow = (Left_2024 + Left_2025) / 23
```

**Rationale:** No growth allowed. Only replacement of workers who leave.

**Example (Egypt):**
```
Stock = 71,536
Recommended_Cap = 71,536 (frozen at stock)
Left_2024 = 9,903
Left_2025 = 8,699
Monthly_Allocation = (9,903 + 8,699) / 23 = 808 workers/month
```

---

### Formula for HIGH DOMINANCE RISK Countries:

If a country has **10 or more dominance alerts**:

```
Recommended_Cap = Current_Stock + (Current_Stock × 0.05)
```

**Rationale:** Conservative 5% buffer to limit concentration risk growth.

---

### Summary Table:

| Condition | Formula | Buffer |
|-----------|---------|--------|
| **Positive Growth** | Stock + Avg_Joiners + (Stock × 0.15) | 15% |
| **Negative Growth (QVC)** | Stock + (Stock × 0.05) | 5% |
| **Negative Growth (Non-QVC)** | Stock (frozen) | 0% |
| **High Dominance (10+ alerts)** | Stock + (Stock × 0.05) | 5% |

---

## 6. Dominance Share (Profession Concentration)

### What is it?
**Dominance Share** measures what percentage of a specific profession is occupied by one nationality. It answers: "How much does this nationality dominate this job?"

### Why is it important?
- Identifies over-reliance on a single nationality for critical jobs
- Helps ensure workforce diversity
- High dominance creates risk if that nationality suddenly leaves or has recruitment problems

### Formula
```
Dominance_Share = Nationality_Workers_in_Profession / Total_Workers_in_Profession × 100
```

### What data do you need?
| Data | How to get it |
|------|---------------|
| **Nationality_Workers_in_Profession** | Count workers of nationality X in profession Y from `07_worker_stock.csv` |
| **Total_Workers_in_Profession** | Count ALL workers (all nationalities combined) in profession Y |

### Important Rules
- Only calculate for professions with **200 or more total workers**
- Only count **long-term workers** (employment >= 1 year)

### Alert Levels
| Level | Threshold | Meaning |
|-------|-----------|---------|
| **WATCH** | >= 30% | Starting to concentrate, monitor closely |
| **HIGH** | >= 40% | Significant concentration, consider diversifying |
| **CRITICAL** | >= 50% | Over half the profession is one nationality, high risk |

### Example
```
Indian Diggers = 2,043
Total Diggers (all nationalities) = 2,855
Dominance = 2,043 / 2,855 × 100 = 71.6%
```
This means 71.6% of all Diggers are Indian → **CRITICAL** alert.

---

## 7. Monthly Outflow

### What is it?
**Monthly Outflow** is the average number of workers leaving each month. It helps predict future capacity that will become available.

### Why is it important?
- For outflow-based countries, this determines monthly allocation capacity
- Helps plan replacement hiring
- Shows how quickly workforce is turning over

### Formula
```
Monthly_Outflow = (Workers_Left_2024 + Workers_Left_2025) / Total_Months
```

### What data do you need?
| Data | How to get it |
|------|---------------|
| **Workers_Left_2024** | Count workers where `employment_end` is in year 2024 |
| **Workers_Left_2025** | Count workers where `employment_end` is in year 2025 |
| **Total_Months** | 12 (2024) + 11 (2025 through November) = 23 months |

### Example
```
Egypt Left 2024 = 9,903
Egypt Left 2025 = 8,699
Monthly Outflow = (9,903 + 8,699) / 23 = 808 workers per month
```

---

## 8. QVC Processing Capacity

### What is it?
**QVC Capacity** is the maximum number of workers that can be processed through the Qatar Visa Center in each country per day.

### Why is it important?
- Determines how quickly new workers can be brought in
- Creates a bottleneck even if cap headroom is available
- Must be considered when planning recruitment

### Formulas
```
Monthly_Capacity = Daily_Capacity × 22 (working days per month)
Annual_Capacity = Daily_Capacity × 264 (working days per year)
```

### Data Source
Daily capacity values are stored in `qvc_capacity.json`.

### Cap Constraint
```
Maximum_Practical_Cap = Current_Stock + Annual_QVC_Capacity
```
Even with headroom, you cannot bring in more workers than QVC can process.

---

## Data Files Summary

| File | What it contains |
|------|------------------|
| `07_worker_stock.csv` | All worker records with employment dates, status, nationality, profession |
| `01_nationalities.csv` | Nationality codes and names lookup |
| `02_professions.csv` | Profession codes and names lookup |
| `qvc_capacity.json` | Daily QVC processing capacity per country |

---

## Nationality Codes Reference

| Country | Numeric Code | Type | Description |
|---------|--------------|------|-------------|
| India | 356 | QVC | Requires visa center processing |
| Bangladesh | 50 | QVC | Requires visa center processing |
| Nepal | 524 | QVC | Requires visa center processing |
| Pakistan | 586 | QVC | Requires visa center processing |
| Philippines | 608 | QVC | Requires visa center processing |
| Sri Lanka | 144 | QVC | Requires visa center processing |
| Egypt | 818 | Outflow | Cap frozen at stock, replacement only |
| Yemen | 886 | Outflow | Cap frozen at stock, replacement only |
| Syria | 760 | Outflow | Cap frozen at stock, replacement only |
| Iran | 364 | Outflow | Cap frozen at stock, replacement only |
| Iraq | 368 | Outflow | Cap frozen at stock, replacement only |
| Afghanistan | 4 | Standard | Non-QVC but uses standard cap recommendations |

---

## Step-by-Step Manual Calculation Guide

### For Each Nationality:

**Step 1: Extract worker data from `07_worker_stock.csv`**
1. Filter by `nationality_code` for your target nationality
2. Calculate employment duration for each worker
3. Remove workers with duration < 365 days (short-term)

**Step 2: Count totals**
- **Current Stock** = Count where `status = 'IN_COUNTRY'`
- **Total_2024** = Count workers active during 2024
- **Total_2025** = Count workers active during 2025
- **Joined_2024** = Count where `employment_start` is in 2024
- **Joined_2025** = Count where `employment_start` is in 2025
- **Left_2024** = Count where `employment_end` is in 2024
- **Left_2025** = Count where `employment_end` is in 2025

**Step 3: Calculate Growth**
```
Growth = (Total_2025 - Total_2024) / Total_2024 × 100
```

**Step 4: Calculate Recommended Cap**
```
IF Growth > 0:
    Avg_Joiners = (Joined_2024 + Joined_2025) / 2
    Recommended_Cap = Stock + Avg_Joiners + (Stock × 0.15)

ELIF country is Non-QVC (EGY, SYR, YEM, IRN, IRQ):
    Recommended_Cap = Stock (frozen)

ELIF dominance_alerts >= 10:
    Recommended_Cap = Stock + (Stock × 0.05)

ELSE:
    Recommended_Cap = Stock + (Stock × 0.05)
```

**Step 5: Calculate other metrics**
```
Utilization = Stock / Recommended_Cap × 100
Headroom = Recommended_Cap - Stock
Monthly_Outflow = (Left_2024 + Left_2025) / 23
```

**Step 6: Calculate Dominance (for each profession)**
1. Count workers of this nationality in each profession
2. Count total workers (all nationalities) in each profession
3. For professions with >= 200 total workers:
   ```
   Dominance = Nationality_Count / Total_Count × 100
   ```
4. Flag alerts: WATCH (30%+), HIGH (40%+), CRITICAL (50%+)

---

## Verification Checklist

After calculating, verify:
- [ ] Growth rates: Negative means declining, positive means growing
- [ ] Recommended Cap: Based on stock + projected demand (not existing cap)
- [ ] Utilization: Should be 0-100% for standard countries, exactly 100% for outflow countries
- [ ] Headroom: Should be 0 for outflow countries, positive for others
- [ ] Dominance: Only calculated for professions with >= 200 workers
- [ ] All calculations exclude short-term workers (< 1 year)

---

*Document updated: January 21, 2026*
