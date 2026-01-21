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
| **Non-QVC Countries** | 6 |
| **Growing Countries** | 2 (Bangladesh, Pakistan) |
| **Declining Countries** | 10 |
| **Short-term Workers Excluded** | 398,678 |
| **Total Dominance Alerts** | 73 |

---

## Section 1: QVC Countries (Visa Center Processing)

These countries require **Qatar Visa Center (QVC)** processing in their home country before workers can travel to Qatar.

### Stock & Capacity Overview

| Country | Stock | Cap | Utilization | Headroom | Growth | QVC/Day |
|---------|------:|----:|------------:|---------:|-------:|--------:|
| India | 488,672 | 676,569 | 72.2% | 204,389 | -11.9% | 800 |
| Bangladesh | 330,602 | 487,741 | 67.8% | 168,296 | +0.9% | 600 |
| Nepal | 317,954 | 437,178 | 72.7% | 129,954 | -9.2% | 400 |
| Pakistan | 158,196 | 242,955 | 65.1% | 90,097 | +0.7% | 500 |
| Philippines | 120,269 | 155,806 | 77.2% | 39,596 | -13.3% | 350 |
| Sri Lanka | 93,238 | 136,111 | 68.5% | 46,019 | -17.4% | 300 |
| **TOTAL QVC** | **1,508,931** | **2,136,360** | **70.6%** | **678,351** | | **2,950** |

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

| Country | Daily Capacity | Monthly Capacity (22 days) | Annual Capacity |
|---------|---------------:|---------------------------:|----------------:|
| India | 800 | 17,600 | 211,200 |
| Bangladesh | 600 | 13,200 | 158,400 |
| Pakistan | 500 | 11,000 | 132,000 |
| Nepal | 400 | 8,800 | 105,600 |
| Philippines | 350 | 7,700 | 92,400 |
| Sri Lanka | 300 | 6,600 | 79,200 |
| **TOTAL** | **2,950** | **64,900** | **778,800** |

---

## Section 2: Non-QVC Countries (Outflow-Based Allocation)

These countries do **NOT** require QVC processing. All have **negative growth** and use **outflow-based allocation**:
- **Cap = Current Stock** (frozen)
- **Monthly capacity = Previous month's outflow** (replacement only)
- **No growth allowed**

### Stock & Capacity Overview

| Country | Stock | Cap | Utilization | Monthly Outflow | Growth | Type |
|---------|------:|----:|------------:|----------------:|-------:|------|
| Egypt | 71,536 | 71,536 | 100% | 808 | -10.8% | OUTFLOW |
| Syria | 23,211 | 23,211 | 100% | 305 | -12.4% | OUTFLOW |
| Yemen | 12,499 | 12,499 | 100% | 70 | -1.3% | OUTFLOW |
| Iran | 6,439 | 6,439 | 100% | 59 | -6.8% | OUTFLOW |
| Afghanistan | 2,297 | 2,297 | 100% | 37 | -9.5% | OUTFLOW |
| Iraq | 1,581 | 1,581 | 100% | 16 | -6.4% | OUTFLOW |
| **TOTAL NON-QVC** | **117,563** | **117,563** | **100%** | **1,295** | | |

### Non-QVC Flow Analysis (2024-2025)

| Country | Left 2024 | Left 2025 | Joined 2024 | Joined 2025 | Net Change |
|---------|----------:|----------:|------------:|------------:|-----------:|
| Egypt | 9,903 | 8,699 | 209 | 3 | -18,390 |
| Syria | 3,612 | 3,405 | 483 | 7 | -6,527 |
| Yemen | 827 | 802 | 844 | 48 | -737 |
| Iran | 647 | 732 | 535 | 16 | -828 |
| Afghanistan | 371 | 492 | 548 | 2 | -313 |
| Iraq | 193 | 189 | 105 | 1 | -276 |

> **Note:** All non-QVC countries show significant net outflow (more leaving than joining), confirming the outflow-based allocation model is appropriate.

---

## Section 3: Dominance Alerts

**Formula:** `Dominance_Share = Nationality_Workers / Total_Workers_in_Profession`  
**Minimum Profession Size:** 200 workers  
**Thresholds:** WATCH >= 30%, HIGH >= 40%, CRITICAL >= 50%

### India (30 alerts)

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

### Bangladesh (23 alerts)

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

### Nepal (8 alerts)

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

### Philippines (9 alerts)

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

### Egypt (2 alerts)

| Level | Profession | Share | Workers |
|-------|------------|------:|--------:|
| CRITICAL | LEGAL PROFESSIONAL | 51.8% | 302/583 |
| HIGH | LAWYER | 46.8% | 363/775 |

### Pakistan (1 alert)

| Level | Profession | Share | Workers |
|-------|------------|------:|--------:|
| CRITICAL | POLICE ARMY STAFF | 55.1% | 4,283/7,777 |

---

## Section 4: Cap Recommendations

### QVC Countries

| Country | Current Cap | Recommended | Change | Reason |
|---------|------------:|------------:|-------:|--------|
| India | 676,569 | 710,397 | +33,828 | High alerts (30) - Conservative |
| Bangladesh | 487,741 | 512,128 | +24,387 | High alerts (23) - Conservative |
| Nepal | 437,178 | 459,036 | +21,858 | High alerts (8) - Conservative |
| Pakistan | 242,955 | 267,250 | +24,295 | Standard moderate (+10%) |
| Philippines | 155,806 | 163,596 | +7,790 | High alerts (9) - Conservative |
| Sri Lanka | 136,111 | 142,235 | +6,124 | Decline > 5% adjustment |

### Non-QVC Countries

| Country | Original Cap | Effective Cap | Status |
|---------|-------------:|--------------:|--------|
| Egypt | 81,668 | 71,536 | **FROZEN** at stock |
| Syria | 27,038 | 23,211 | **FROZEN** at stock |
| Yemen | 14,949 | 12,499 | **FROZEN** at stock |
| Iran | 7,768 | 6,439 | **FROZEN** at stock |
| Afghanistan | 3,016 | 2,297 | **FROZEN** at stock |
| Iraq | 1,959 | 1,581 | **FROZEN** at stock |

> **Policy:** Non-QVC countries with negative growth have their cap frozen at current stock level. Monthly allocation is based solely on outflow (replacement model).

---

## Section 5: Key Insights & Recommendations

### Growth Analysis

| Status | Countries | Notes |
|--------|-----------|-------|
| **Growing** | Bangladesh (+0.9%), Pakistan (+0.7%) | Only 2 of 12 countries |
| **Moderate Decline** | Yemen (-1.3%), Iraq (-6.4%), Iran (-6.8%) | Manageable decline |
| **Significant Decline** | Nepal (-9.2%), Afghanistan (-9.5%), Egypt (-10.8%) | Concerning trend |
| **Severe Decline** | India (-11.9%), Syria (-12.4%), Philippines (-13.3%), Sri Lanka (-17.4%) | Requires attention |

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
