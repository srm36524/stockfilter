import pandas as pd
import os
from datetime import datetime
from github import Github

# -----------------------
# CONFIG
# -----------------------
STOCK_CSV = "Github_Stocks.csv"
BSE_FOLDER = "./bhavcopy_bse/"
NSE_FOLDER = "./bhavcopy_nse/"
GITHUB_TOKEN = "YOUR_PERSONAL_ACCESS_TOKEN"
REPO_NAME = "username/repo_name"
CACHE_FILE_PATH = "stock_price_volume.csv"

# -----------------------
# Load stock list
# -----------------------
df_stocks = pd.read_csv(STOCK_CSV)
df_stocks.columns = df_stocks.columns.str.strip()

# -----------------------
# Process BSE files
# -----------------------
bse_files = [f for f in os.listdir(BSE_FOLDER) if f.endswith("_BSE.csv")]
dfs = []

for file in bse_files:
    date_str = file.split("_")[0]
    file_date = datetime.strptime(date_str, "%Y%m%d").date()
    df_bse = pd.read_csv(os.path.join(BSE_FOLDER, file))
    df_bse = df_bse[df_bse['SC_CODE'].isin(df_stocks['Code'])]  # filter stocks
    df_bse = df_bse[['SC_CODE','CLOSE','NO_OF_SHRS']]
    df_bse.rename(columns={'SC_CODE':'Code','CLOSE':'Close','NO_OF_SHRS':'Volume'}, inplace=True)
    df_bse['Date'] = file_date
    df_bse['Exchange'] = 'BSE'
    dfs.append(df_bse)

# -----------------------
# Process NSE files
# -----------------------
nse_files = [f for f in os.listdir(NSE_FOLDER) if f.endswith("_NSE.csv")]

for file in nse_files:
    date_str = file.split("_")[0]
    file_date = datetime.strptime(date_str, "%Y%m%d").date()
    df_nse = pd.read_csv(os.path.join(NSE_FOLDER, file))
    df_nse = df_nse[df_nse['SYMBOL'].isin(df_stocks['Code'])]
    df_nse = df_nse[['SYMBOL','CLOSE','TOTTRDQTY']]
    df_nse.rename(columns={'SYMBOL':'Code','CLOSE':'Close','TOTTRDQTY':'Volume'}, inplace=True)
    df_nse['Date'] = file_date
    df_nse['Exchange'] = 'NSE'
    dfs.append(df_nse)

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
