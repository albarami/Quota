# Comprehensive Quota System Report

**Report Generated:** January 21, 2026  
**Data Source:** Ministry Real Data (`real_data/`)  
**Filter Applied:** Long-term workers only (employment >= 1 year)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Long-term Workers** | 1,626,494 |
| **Total Effective Cap** | 2,253,923 |
| **Overall Utilization** | 72.2% |
| **QVC Countries** | 6 |
| **Non-QVC Outflow-Based Countries** | 5 |
| **Growing Countries** | 0 |
| **Declining Countries** | 12 (all countries) |
| **Short-term Workers Excluded** | 398,678 |
| **Total Dominance Alerts** | 278 |

---

## Section 1: QVC Countries (Visa Center Processing)

These countries require **Qatar Visa Center (QVC)** processing in their home country before workers can travel to Qatar.

### Stock & Capacity Overview

| Country | Stock | Cap | Utilization | Headroom | Growth | QVC/Day |
|---------|------:|----:|------------:|---------:|-------:|--------:|
| India | 488,672 | 676,569 | 72.2% | 204,389 | -20.7% | 805 |
| Bangladesh | 330,602 | 487,741 | 67.8% | 168,296 | -14.0% | 515 |
| Nepal | 317,954 | 437,178 | 72.7% | 129,954 | -18.5% | 325 |
| Pakistan | 158,196 | 242,955 | 65.1% | 90,097 | -20.8% | 370 |
| Philippines | 120,269 | 155,806 | 77.2% | 39,596 | -17.8% | 280 |
| Sri Lanka | 93,238 | 136,111 | 68.5% | 46,019 | -22.2% | 150 |
| **TOTAL QVC** | **1,508,931** | **2,136,360** | **70.6%** | **678,351** | | **2,445** |

### QVC Flow Analysis (2024-2025)

| Country | Left 2024 | Left 2025 | Joined 2024 | Joined 2025 | Monthly Outflow |
|---------|----------:|----------:|------------:|------------:|----------------:|
| India | 157,395 | 109,767 | 56,799 | 1,373 | 11,615 |
| Bangladesh | 66,236 | 63,038 | 66,697 | 2,086 | 5,620 |
| Nepal | 87,984 | 62,985 | 32,360 | 1,586 | 6,563 |
| Pakistan | 52,014 | 35,175 | 27,492 | 1,116 | 3,790 |
| Philippines | 31,611 | 25,256 | 10,401 | 180 | 2,472 |
| Sri Lanka | 35,068 | 28,551 | 10,362 | 345 | 2,766 |

### QVC Processing Capacity

*Source: `real_data/qvc_capacity.json`*

| Country | Daily Capacity | Monthly Capacity (22 days) | Annual Capacity |
|---------|---------------:|---------------------------:|----------------:|
| India | 805 | 17,710 | 212,520 |
| Bangladesh | 515 | 11,330 | 135,960 |
| Pakistan | 370 | 8,140 | 97,680 |
| Nepal | 325 | 7,150 | 85,800 |
| Philippines | 280 | 6,160 | 73,920 |
| Sri Lanka | 150 | 3,300 | 39,600 |
| **TOTAL** | **2,445** | **53,790** | **645,480** |

---

## Section 2: Non-QVC Countries (Outflow-Based Allocation)

These 5 countries do **NOT** require QVC processing and use **outflow-based allocation**:
- **Cap = Current Stock** (frozen)
- **Monthly capacity = Previous month's outflow** (replacement only)
- **No growth allowed**

### Stock & Capacity Overview (5 Outflow-Based Countries)

| Country | Stock | Cap | Utilization | Monthly Outflow | Growth | Type |
|---------|------:|----:|------------:|----------------:|-------:|------|
| Egypt | 71,536 | 71,536 | 100% | 808 | -11.0% | OUTFLOW |
| Syria | 23,211 | 23,211 | 100% | 305 | -11.9% | OUTFLOW |
| Yemen | 12,499 | 12,499 | 100% | 70 | -5.5% | OUTFLOW |
| Iran | 6,439 | 6,439 | 100% | 59 | -8.1% | OUTFLOW |
| Iraq | 1,581 | 1,581 | 100% | 16 | -9.8% | OUTFLOW |
| **TOTAL OUTFLOW** | **115,266** | **115,266** | **100%** | **1,258** | | |

### Afghanistan (Standard Cap - NOT Outflow-Based)

| Country | Stock | Cap | Utilization | Headroom | Growth | Type |
|---------|------:|----:|------------:|---------:|-------:|------|
| Afghanistan | 2,297 | 3,016 | 76.2% | 796 | -11.7% | **Standard** |

> **Note:** Afghanistan uses standard cap recommendations (NOT outflow-based) despite negative growth. It is the only non-QVC country with standard cap treatment.

### Non-QVC Flow Analysis (2024-2025)

| Country | Left 2024 | Left 2025 | Joined 2024 | Joined 2025 | Net Change |
|---------|----------:|----------:|------------:|------------:|-----------:|
| Egypt | 9,903 | 8,699 | 209 | 3 | -18,390 |
| Syria | 3,612 | 3,405 | 483 | 7 | -6,527 |
| Yemen | 827 | 802 | 844 | 48 | -737 |
| Iran | 647 | 732 | 535 | 16 | -828 |
| Iraq | 193 | 189 | 105 | 1 | -276 |

> **Note:** These 5 non-QVC countries show significant net outflow (more leaving than joining), confirming the outflow-based allocation model is appropriate.

---

## Section 3: Dominance Alerts

**Formula:** `Dominance_Share = Nationality_Workers / Total_Workers_in_Profession`  
**Minimum Profession Size:** 200 workers  
**Thresholds:** WATCH >= 30%, HIGH >= 40%, CRITICAL >= 50%

### Summary by Nationality

| Nationality | Total Alerts | CRITICAL | HIGH | WATCH |
|-------------|-------------:|---------:|-----:|------:|
| India | 136 | 20 | 31 | 85 |
| Bangladesh | 78 | 26 | 24 | 28 |
| Nepal | 31 | 1 | 8 | 22 |
| Philippines | 25 | 6 | 9 | 10 |
| Egypt | 6 | 1 | 2 | 3 |
| Pakistan | 1 | 1 | 0 | 0 |
| Sri Lanka | 1 | 0 | 0 | 1 |
| **TOTAL** | **278** | **55** | **74** | **149** |

### India (136 alerts - Top 10)

| Level | Profession | Share | Workers |
|-------|------------|------:|--------:|
| CRITICAL | DIGGER | 71.6% | 2,043/2,855 |
| CRITICAL | SEAMEN | 65.7% | 3,591/5,464 |
| CRITICAL | Mechanical Technician | 58.5% | 3,735/6,389 |
| CRITICAL | PETROCHEMICALS | 55.5% | 4,031/7,260 |
| CRITICAL | MECHAN ENGINEER | 53.3% | 1,974/3,703 |
| CRITICAL | WELD TECHNICIAN | 52.9% | 2,458/4,649 |
| HIGH | PIPE FITTER | 46.4% | 2,460/5,298 |
| HIGH | SALES EXECUTIVE | 46.4% | 2,060/4,438 |
| HIGH | TECHNICIAN GEN | 46.3% | 5,492/11,866 |
| HIGH | ELECT ENGINEER | 46.1% | 2,044/4,433 |

### Bangladesh (78 alerts - Top 10)

| Level | Profession | Share | Workers |
|-------|------------|------:|--------:|
| CRITICAL | ASST EXECUTIVE MAN | 91.0% | 3,474/3,816 |
| CRITICAL | ADMIN MANAGER | 69.4% | 8,283/11,933 |
| CRITICAL | ADMINIS CONSULT | 66.4% | 1,562/2,352 |
| CRITICAL | General civil engineer | 65.7% | 1,332/2,028 |
| CRITICAL | ACCOUNTANT (GEN) | 64.7% | 8,324/12,863 |
| CRITICAL | SHEPHERD | 53.8% | 2,002/3,719 |
| CRITICAL | FARMER | 50.8% | 2,614/5,144 |
| HIGH | MARKET MANAGER | 49.7% | 2,505/5,045 |
| HIGH | ASSISTANT MANAGER | 45.9% | 1,417/3,089 |
| HIGH | ADMIN DIRECTOR | 45.4% | 5,691/12,543 |

### Nepal (31 alerts - Top 10)

| Level | Profession | Share | Workers |
|-------|------------|------:|--------:|
| HIGH | BUILDING WORKER | 49.8% | 4,098/8,237 |
| HIGH | LABOURER | 49.3% | 109,356/222,017 |
| HIGH | GEN CLEAN WORKER | 45.4% | 32,397/71,323 |
| HIGH | TAILOR | 44.5% | 3,040/6,828 |
| WATCH | DRY CLEAN WORKER | 37.8% | 728/1,925 |
| WATCH | PACKING WORKER | 33.1% | 841/2,538 |
| WATCH | WASHING WORKER | 32.5% | 917/2,820 |
| WATCH | PLASTER WORKER | 32.3% | 2,157/6,673 |

### Philippines (25 alerts - Top 10)

| Level | Profession | Share | Workers |
|-------|------------|------:|--------:|
| CRITICAL | Care Giver | 88.6% | 1,203/1,358 |
| CRITICAL | MANICURIST | 64.2% | 436/679 |
| CRITICAL | Assistant teacher | 50.1% | 433/864 |
| HIGH | BEAUTICIAN | 45.1% | 679/1,505 |
| HIGH | HAIR BEAUTICIAN | 41.8% | 1,288/3,081 |
| WATCH | SECRETARY | 39.9% | 3,645/9,144 |
| WATCH | SERVANT | 38.1% | 2,566/6,735 |
| WATCH | Cosmetologist | 34.7% | 437/1,259 |
| WATCH | NURSE | 33.7% | 7,683/22,830 |

### Egypt (6 alerts)

| Level | Profession | Share | Workers |
|-------|------------|------:|--------:|
| CRITICAL | LEGAL PROFESSIONAL | 51.8% | 302/583 |
| HIGH | LAWYER | 46.8% | 363/775 |
| HIGH | SOCIAL SPECIALIST | 41.7% | 86/206 |
| WATCH | AGRICULTURAL ENGIN | 31.2% | 114/365 |
| WATCH | AWP | 31.2% | 67/215 |
| WATCH | LEGAL CONSULTANT | 30.0% | 94/313 |

### Pakistan (1 alert)

| Level | Profession | Share | Workers |
|-------|------------|------:|--------:|
| CRITICAL | POLICE ARMY STAFF | 55.1% | 4,283/7,777 |

---

## Section 4: Cap Recommendations (Data-Driven)

**Formula:** Based on Stock + Projected Demand + Buffer (NO pre-existing caps)

### QVC Countries

| Country | Stock | Recommended Cap | Headroom | Reason |
|---------|------:|----------------:|---------:|--------|
| India | 488,672 | 513,105 | +24,433 | High alerts (136) - 5% buffer |
| Bangladesh | 330,602 | 347,132 | +16,530 | High alerts (78) - 5% buffer |
| Nepal | 317,954 | 333,851 | +15,897 | High alerts (31) - 5% buffer |
| Pakistan | 158,196 | 166,105 | +7,909 | Decline -20.8% - 5% buffer |
| Philippines | 120,269 | 126,282 | +6,013 | High alerts (25) - 5% buffer |
| Sri Lanka | 93,238 | 97,899 | +4,661 | Decline -22.2% - 5% buffer |

### Non-QVC Countries (Outflow-Based - 5 countries)

| Country | Stock | Recommended Cap | Headroom | Status |
|---------|------:|----------------:|---------:|--------|
| Egypt | 71,536 | 71,536 | 0 | **FROZEN** at stock |
| Syria | 23,211 | 23,211 | 0 | **FROZEN** at stock |
| Yemen | 12,499 | 12,499 | 0 | **FROZEN** at stock |
| Iran | 6,439 | 6,439 | 0 | **FROZEN** at stock |
| Iraq | 1,581 | 1,581 | 0 | **FROZEN** at stock |

> **Policy:** Non-QVC countries with negative growth have cap frozen at stock. Monthly allocation = outflow only.

### Afghanistan (Standard Cap - NOT Outflow-Based)

| Country | Stock | Recommended Cap | Headroom | Reason |
|---------|------:|----------------:|---------:|--------|
| Afghanistan | 2,297 | 2,411 | +114 | Decline -11.7% - 5% buffer |

> **Note:** Afghanistan uses standard cap recommendations, not outflow-based allocation.

### Cap Formula Summary

| Condition | Formula | Buffer |
|-----------|---------|--------|
| **Positive Growth** | Stock + Avg_Joiners + (Stock × 0.15) | 15% |
| **Negative Growth + High Alerts** | Stock + (Stock × 0.05) | 5% |
| **Negative Growth (QVC)** | Stock + (Stock × 0.05) | 5% |
| **Non-QVC Outflow-Based** | Stock (frozen) | 0% |

---

## Section 5: Key Insights & Recommendations

### Growth Analysis

**Formula:** `Growth = (Total_2025 - Total_2024) / Total_2024 × 100`  
**Total** = Workers active during each year (long-term only, >= 1 year employment)

| Status | Countries | Notes |
|--------|-----------|-------|
| **Moderate Decline (5-12%)** | Yemen (-5.5%), Iran (-8.1%), Iraq (-9.8%), Egypt (-11.0%), Afghanistan (-11.7%), Syria (-11.9%) | Manageable |
| **Significant Decline (12-20%)** | Bangladesh (-14.0%), Philippines (-17.8%), Nepal (-18.5%) | Concerning |
| **Severe Decline (>20%)** | India (-20.7%), Pakistan (-20.8%), Sri Lanka (-22.2%) | Requires urgent attention |

### Risk Areas

1. **India** has 30 dominance alerts - highest concentration risk
2. **Bangladesh** has 23 alerts with very high shares in management roles (91% in ASST EXECUTIVE MAN)
3. **Nepal** dominates labor-intensive roles (49% of all LABOURERS)
4. **Philippines** dominates caregiving (88.6% of Care Givers)

### Recommendations

1. **Monitor India & Bangladesh closely** - High dominance alerts suggest over-reliance on these nationalities in specific professions
2. **Diversify recruitment** in dominated professions to reduce single-nationality dependency
3. **Maintain outflow-based allocation** for all non-QVC countries until growth turns positive
4. **Review QVC capacity** - Current combined capacity of 2,950/day may be limiting growth for QVC countries

---

## Appendix: Data Quality Notes

- **Total records processed:** 4,036,347
- **Short-term excluded:** 398,678 (employment < 1 year)
- **Long-term workers analyzed:** 1,626,494
- **Data period:** 2024-2025
- **Last updated:** January 21, 2026

---

*Report generated by `scripts/comprehensive_report.py`*
