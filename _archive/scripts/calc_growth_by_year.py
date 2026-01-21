"""
Calculate growth by comparing total workers in 2024 vs 2025 for all 12 nationalities.
Excludes short-term workers (employment < 1 year).
"""
import pandas as pd
from datetime import datetime

# Minimum employment duration (365 days = 1 year)
MIN_EMPLOYMENT_DAYS = 365

# Read the worker stock file
worker_file = r'D:\Quota\real_data\07_worker_stock.csv'

print('Loading worker data...')
df = pd.read_csv(worker_file, low_memory=False)
print(f'Total records: {len(df):,}')

# Define year boundaries
year_2024_start = pd.Timestamp('2024-01-01')
year_2024_end = pd.Timestamp('2024-12-31')
year_2025_start = pd.Timestamp('2025-01-01')
year_2025_end = pd.Timestamp('2025-12-31')
today = pd.Timestamp.now()

# Convert date columns
df['emp_start'] = pd.to_datetime(df['employment_start'], errors='coerce')
df['emp_end'] = pd.to_datetime(df['employment_end'], errors='coerce')

# Calculate employment duration and filter short-term workers
# For workers still employed (no end date), use today as end date
df['duration'] = (df['emp_end'].fillna(today) - df['emp_start']).dt.days
df = df[df['duration'] >= MIN_EMPLOYMENT_DAYS]
print(f'Long-term workers (>= 1 year): {len(df):,}')

# All 12 nationalities - using INTEGER codes from actual data
NATIONALITY_CODES = {
    'IND': 356, 'BGD': 50, 'NPL': 524, 'PAK': 586,
    'PHL': 608, 'LKA': 144, 'EGY': 818, 'YEM': 886,
    'SYR': 760, 'AFG': 4, 'IRN': 364, 'IRQ': 368
}

print()
print('=' * 70)
print('WORKERS BY YEAR - ALL 12 NATIONALITIES')
print('=' * 70)
print(f"{'Country':<15} {'2024':>12} {'2025':>12} {'Change':>10} {'Growth':>10}")
print('-' * 70)

results = {}

for name, code in NATIONALITY_CODES.items():
    nat_df = df[df['nationality_code'] == code]
    
    # Active in 2024: started <= end of 2024 AND (no end OR ended >= start of 2024)
    active_2024 = nat_df[
        (nat_df['emp_start'] <= year_2024_end) & 
        ((nat_df['emp_end'].isna()) | (nat_df['emp_end'] >= year_2024_start))
    ]
    
    # Active in 2025: started <= end of 2025 AND (no end OR ended >= start of 2025)
    active_2025 = nat_df[
        (nat_df['emp_start'] <= year_2025_end) & 
        ((nat_df['emp_end'].isna()) | (nat_df['emp_end'] >= year_2025_start))
    ]
    
    count_2024 = len(active_2024)
    count_2025 = len(active_2025)
    change = count_2025 - count_2024
    growth = ((count_2025 - count_2024) / count_2024 * 100) if count_2024 > 0 else 0
    
    results[name] = {
        'total_2024': count_2024,
        'total_2025': count_2025,
        'change': change,
        'growth': growth
    }
    
    print(f"{name:<15} {count_2024:>12,} {count_2025:>12,} {change:>+10,} {growth:>+9.1f}%")

print('=' * 70)

# Save results to JSON for use in other scripts
import json
with open(r'D:\Quota\real_data\growth_by_year.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to: D:\\Quota\\real_data\\growth_by_year.json")
