#!/usr/bin/env python
"""Read Excel file with multiple sheets."""

import pandas as pd

# Read the Excel file
file_path = 'data/VP_2025_QVC.xlsx'

# Get sheet names
xl = pd.ExcelFile(file_path)
print(f"File: {file_path}")
print(f"Sheet names: {xl.sheet_names}")
print()

# Read each sheet
for sheet_name in xl.sheet_names:
    print("=" * 80)
    print(f"SHEET: {sheet_name}")
    print("=" * 80)
    
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print()
    print("COLUMNS:")
    for i, col in enumerate(df.columns):
        print(f"  {i+1}. {col}")
    print()
    
    print("FIRST 20 ROWS:")
    print("-" * 80)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)
    print(df.head(20).to_string())
    print()
    
    print("DATA TYPES:")
    print(df.dtypes)
    print()
    
    # Summary statistics for numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        print("NUMERIC SUMMARY:")
        print(df[numeric_cols].describe())
    print()
    print()
