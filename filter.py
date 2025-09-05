import pandas as pd
import os
from datetime import datetime
from github import Github

# -----------------------
# CONFIG
# -----------------------
STOCK_CSV = "Github_Stocks.csv"
BHAVCOPY_FOLDER = "./bhavcopy_all/"  # all BSE & NSE CSVs in this folder
GITHUB_TOKEN = "YOUR_PERSONAL_ACCESS_TOKEN"
REPO_NAME = "username/repo_name"
CACHE_FILE_PATH = "stock_price_volume.csv"

# -----------------------
# Load stock list
# -----------------------
df_stocks = pd.read_csv(STOCK_CSV)
df_stocks.columns = df_stocks.columns.str.strip()

# -----------------------
# Process all files
# -----------------------
all_files = [f for f in os.listdir(BHAVCOPY_FOLDER) if f.endswith(".csv") and "Github_Stocks" not in f]
dfs = []

for file in all_files:
    date_str = file.split("_")[0]
    file_date = datetime.strptime(date_str, "%Y%m%d").date()
    df = pd.read_csv(os.path.join(BHAVCOPY_FOLDER, file))
    
    if "_BSE" in file:
        df = df[df['SC_CODE'].isin(df_stocks['Code'])]
        df = df[['SC_CODE','CLOSE','NO_OF_SHRS']]
        df.rename(columns={'SC_CODE':'Code','CLOSE':'Close','NO_OF_SHRS':'Volume'}, inplace=True)
        df['Exchange'] = 'BSE'
    elif "_NSE" in file:
        df = df[df['SYMBOL'].isin(df_stocks['Code'])]
        df = df[['SYMBOL','CLOSE','TOTTRDQTY']]
        df.rename(columns={'SYMBOL':'Code','CLOSE':'Close','TOTTRDQTY':'Volume'}, inplace=True)
        df['Exchange'] = 'NSE'
    else:
        continue  # skip unrelated CSVs

    df['Date'] = file_date
    dfs.append(df)

# -----------------------
# Combine all data
# -----------------------
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
except:
    repo.create_file(CACHE_FILE_PATH, f"Create price-volume cache {datetime.today().date()}", csv_data)

print("Price+volume cache pushed to GitHub successfully!")
