import pandas as pd
import os
import re
from datetime import datetime
from github import Github

# -----------------------
# CONFIG
# -----------------------
STOCK_CSV = "Github_Stocks.csv"  # stock list CSV
GITHUB_TOKEN = "YOUR_PERSONAL_ACCESS_TOKEN"
REPO_NAME = "username/repo_name"
CACHE_FILE_PATH = "stock_price_volume.csv"

# -----------------------
# Load stock list
# -----------------------
df_stocks = pd.read_csv(STOCK_CSV)
df_stocks.columns = df_stocks.columns.str.strip()

# -----------------------
# Process all bhavcopy CSVs in the main folder
# -----------------------
all_files = [f for f in os.listdir(".") if f.endswith(".csv") and f != STOCK_CSV]
dfs = []

for file in all_files:
    # Check if filename starts with 8 digits (YYYYMMDD)
    match = re.match(r"(\d{8})", file)
    if not match:
        print(f"Skipping file (no valid date found): {file}")
        continue
    
    date_str = match.group(1)
    try:
        file_date = datetime.strptime(date_str, "%Y%m%d").date()
    except ValueError:
        print(f"Skipping file (invalid date format): {file}")
        continue
    
    df = pd.read_csv(file)

    # Detect BSE vs NSE based on columns
    if 'SC_CODE' in df.columns:
        df = df[df['SC_CODE'].isin(df_stocks['Code'])]
        df = df[['SC_CODE','CLOSE','NO_OF_SHRS']]
        df.rename(columns={'SC_CODE':'Code','CLOSE':'Close','NO_OF_SHRS':'Volume'}, inplace=True)
        df['Exchange'] = 'BSE'
    elif 'SYMBOL' in df.columns:
        df = df[df['SYMBOL'].isin(df_stocks['Code'])]
        df = df[['SYMBOL','CLOSE','TOTTRDQTY']]
        df.rename(columns={'SYMBOL':'Code','CLOSE':'Close','TOTTRDQTY':'Volume'}, inplace=True)
        df['Exchange'] = 'NSE'
    else:
        print(f"Skipping file (unknown format): {file}")
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

# -----------------------
# Calculate daily change
# -----------------------
df_all['Daily_Change'] = df_all.groupby(['Code','Exchange'])['Close'].diff()

# -----------------------
# Keep last 9 days
# -----------------------
df_all = df_all.groupby(['Code','Exchange']).tail(9)

# -----------------------
# Save locally
# -----------------------
df_all.to_csv(CACHE_FILE_PATH, index=False)
print("Local price+volume cache saved.")

# -----------------------
# Push to GitHub
# -----------------------
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)
csv_data = df_all.to_csv(index=False)

try:
    contents = repo.get_contents(CACHE_FILE_PATH)
    repo.update_file(contents.path, f"Update price-volume cache {datetime.today().date()}", csv_data, contents.sha)
    print("Price+volume cache updated on GitHub successfully!")
except:
    repo.create_file(CACHE_FILE_PATH, f"Create price-volume cache {datetime.today().date()}", csv_data)
    print("Price+volume cache created on GitHub successfully!")
