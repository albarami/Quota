"""Check if we can identify short-term vs long-term permits in the data."""
import pandas as pd

df = pd.read_csv('real_data/07_worker_stock.csv')
df['employment_start'] = pd.to_datetime(df['employment_start'], errors='coerce')
df['employment_end'] = pd.to_datetime(df['employment_end'], errors='coerce')
df['visa_issue_date'] = pd.to_datetime(df['visa_issue_date'], errors='coerce')
df['visa_expiry_date'] = pd.to_datetime(df['visa_expiry_date'], errors='coerce')

print('DATA AVAILABILITY:')
print(f'Total records: {len(df):,}')
print(f'Has employment_start: {df["employment_start"].notna().sum():,}')
print(f'Has employment_end: {df["employment_end"].notna().sum():,}')
print(f'Has visa_issue_date: {df["visa_issue_date"].notna().sum():,}')
print(f'Has visa_expiry_date: {df["visa_expiry_date"].notna().sum():,}')

# Check employment duration for those who have both dates
has_both = df[(df['employment_start'].notna()) & (df['employment_end'].notna())].copy()
if len(has_both) > 0:
    has_both['duration_days'] = (has_both['employment_end'] - has_both['employment_start']).dt.days
    print(f'\nEMPLOYMENT DURATION (for {len(has_both):,} with both dates):')
    print(f'  Min: {has_both["duration_days"].min()} days')
    print(f'  Max: {has_both["duration_days"].max()} days')
    print(f'  Avg: {has_both["duration_days"].mean():.0f} days ({has_both["duration_days"].mean()/365:.1f} years)')
    print(f'  Median: {has_both["duration_days"].median():.0f} days')
    
    # Distribution
    print('\n  Duration distribution:')
    short_term = (has_both['duration_days'] < 365).sum()
    one_two = ((has_both['duration_days'] >= 365) & (has_both['duration_days'] < 730)).sum()
    two_five = ((has_both['duration_days'] >= 730) & (has_both['duration_days'] < 1825)).sum()
    five_plus = (has_both['duration_days'] >= 1825).sum()
    
    print(f'    < 1 year (SHORT-TERM): {short_term:,} ({short_term/len(has_both)*100:.1f}%)')
    print(f'    1-2 years: {one_two:,} ({one_two/len(has_both)*100:.1f}%)')
    print(f'    2-5 years: {two_five:,} ({two_five/len(has_both)*100:.1f}%)')
    print(f'    5+ years (LONG-TERM): {five_plus:,} ({five_plus/len(has_both)*100:.1f}%)')

# Check profession codes - might indicate permit type
print('\n\nCHECKING PROFESSION CODES:')
prof_df = pd.read_csv('real_data/02_professions.csv')
print(f'Total professions: {len(prof_df)}')
print('\nProfession columns:')
print(prof_df.columns.tolist())
print('\nSample professions:')
print(prof_df.head(10))
