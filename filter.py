import pandas as pd
import os
import re
from datetime import datetime

# -----------------------
# CONFIG
# -----------------------
STOCK_CSV = "Github_Stocks.csv"  # stock list CSV
CACHE_FILE_PATH = "stock_price_volume.csv"

# -----------------------
# Load stock list
# -----------------------
df_stocks = pd.read_csv(STOCK_CSV)
df_stocks.columns = df_stocks.columns.str.strip()
print(f"Loaded {len(df_stocks)} stocks from {STOCK_CSV}")

# -----------------------
# Process all bhavcopy CSVs in the main folder
# -----------------------
all_files = [f for f in os.listdir(".") if f.endswith(".csv") and f != STOCK_CSV]
dfs = []

for idx, file in enumerate(all_files, 1):
    print(f"\n[{idx}/{len(all_files)}] Processing file: {file}")
    
    # Only process files starting with 8-digit date
    match = re.match(r"(\d{8})", file)
    if not match:
        print(f"  Skipping (no valid date found)")
        continue
    
    date_str = match.group(1)
    try:
        file_date = datetime.strptime(date_str, "%Y%m%d").date()
    except ValueError:
        print(f"  Skipping (invalid date format)")
        continue

    df = pd.read_csv(file)
    print(f"  Original rows: {len(df)}")

    # Detect BSE vs NSE based on columns
    if 'SC_CODE' in df.columns:
        df = df[df['SC_CODE'].isin(df_stocks['Code'])]
        df = df[['SC_CODE','CLOSE','NO_OF_SHRS']]
        df.rename(columns={'SC_CODE':'Code','CLOSE':'Close','NO_OF_SHRS':'Volume'}, inplace=True)
        df['Exchange'] = 'BSE'
        print(f"  BSE rows after filter: {len(df)}")
    elif 'SYMBOL' in df.columns:
        df = df[df['SYMBOL'].isin(df_stocks['Code'])]
        df = df[['SYMBOL','CLOSE','TOTTRDQTY']]
        df.rename(columns={'SYMBOL':'Code','CLOSE':'Close','TOTTRDQTY':'Volume'}, inplace=True)
        df['Exchange'] = 'NSE'
        print(f"  NSE rows after filter: {len(df)}")
    else:
        print(f"  Skipping (unknown format)")
        continue

    df['Date'] = file_date
    dfs.append(df)

# -----------------------
# Combine all data
# -----------------------
if not dfs:
    raise ValueError("No valid bhavcopy CSV files found in the folder.")

df_all = pd.concat(dfs)
df_all = df_all.sort_values(['Code','Exchange','Date'])
print(f"\nTotal rows combined: {len(df_all)}")

# -----------------------
# Calculate daily change
# -----------------------
df_all['Daily_Change'] = df_all.groupby(['Code','Exchange'])['Close'].diff()

# -----------------------
# Keep last 9 days
# -----------------------
df_all = df_all.groupby(['Code','Exchange']).tail(9)
print(f"Rows after keeping last 9 days per stock: {len(df_all)}")

# -----------------------
# Save locally (optional)
# -----------------------
df_all.to_csv(CACHE_FILE_PATH, index=False)
print(f"\nLocal price+volume cache saved: {CACHE_FILE_PATH}")

# -----------------------
# Show sample
# -----------------------
print("\nSample data:")
print(df_all.head(10))
