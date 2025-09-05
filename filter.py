import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from github import Github

st.title("Stocks with Continuous Positive Change (GitHub Cached)")

# -------------------------------
# CONFIG: GitHub Repo & CSV
# -------------------------------
GITHUB_TOKEN = "YOUR_PERSONAL_ACCESS_TOKEN"  # GitHub token with repo access
REPO_NAME = "username/repo_name"             # e.g., "SRM/stock-cache"
CACHE_FILE_PATH = "stock_data.csv"          # path in repo
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{CACHE_FILE_PATH}"

# -------------------------------
# Load stock list
# -------------------------------
df_stocks = pd.read_csv("Github_Stocks.csv")
df_stocks.columns = df_stocks.columns.str.strip()
df_stocks = df_stocks[df_stocks['Symbol3'].notnull()]

st.write(f"Total stocks in list: {len(df_stocks)}")
st.dataframe(df_stocks.head())

# -------------------------------
# Load cache from GitHub (if exists)
# -------------------------------
try:
    df_cache = pd.read_csv(GITHUB_RAW_URL, parse_dates=['Date'])
    st.write(f"Loaded cache from GitHub: {len(df_cache)} records")
except:
    st.write("Cache not found. Starting fresh.")
    df_cache = pd.DataFrame(columns=['Symbol3', 'Date', 'Close', 'Volume'])

# -------------------------------
# Update cache with latest data
# -------------------------------
st.write("Updating cache with latest data...")

# Determine last date in cache
if not df_cache.empty:
    last_date = df_cache['Date'].max()
else:
    last_date = datetime.today() - timedelta(days=10)

new_data_list = []
for symbol in df_stocks['Symbol3']:
    ticker = f"{symbol}.NS"  # Adjust if exchange info is available
    try:
        df = yf.download(ticker, start=last_date + timedelta(days=1),
                         end=datetime.today() + timedelta(days=1), progress=False)
        if df.empty:
            continue
        df_reset = df.reset_index()[['Date','Close','Volume']]
        df_reset['Symbol3'] = symbol
        new_data_list.append(df_reset)
    except Exception as e:
        st.write(f"Skipped {ticker}: {e}")

# Append new data and keep last 10 days per stock
if new_data_list:
    df_new = pd.concat(new_data_list)
    df_cache = pd.concat([df_cache, df_new])
    df_cache = df_cache.sort_values(['Symbol3','Date']).groupby('Symbol3').tail(10)
else:
    st.write("No new data to update.")

st.write(f"Cache updated: {len(df_cache)} records")

# -------------------------------
# Submit button for filtering
# -------------------------------
n_days = st.number_input("Select number of consecutive positive days", min_value=1, max_value=10, value=3, step=1)
submit = st.button("Submit")

if submit:
    results = []
    for symbol in df_stocks['Symbol3']:
        df_symbol = df_cache[df_cache['Symbol3'] == symbol].sort_values('Date')
        if len(df_symbol) < n_days:
            continue
        daily_change = df_symbol['Close'].diff().tail(n_days)
        if (daily_change > 0).all():
            last_row = df_symbol.iloc[-1]
            results.append({
                'Symbol3': symbol,
                'Last_Close': last_row['Close'],
                'Last_Volume': last_row['Volume'],
                'Daily_Change': daily_change.to_dict()
            })
    if results:
        st.success(f"Found {len(results)} stocks with continuous positive change for {n_days} days.")
        st.dataframe(pd.DataFrame(results))
    else:
        st.warning(f"No stocks found with continuous positive change for {n_days} days.")

# -------------------------------
# Push updated cache back to GitHub
# -------------------------------
if not df_cache.empty:
    st.write("Pushing updated cache to GitHub...")
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        csv_data = df_cache.to_csv(index=False)

        # Check if file exists
        try:
            contents = repo.get_contents(CACHE_FILE_PATH)
            repo.update_file(contents.path, f"Update stock cache {datetime.today().date()}", csv_data, contents.sha)
        except:
            repo.create_file(CACHE_FILE_PATH, f"Create stock cache {datetime.today().date()}", csv_data)

        st.success("Cache successfully updated on GitHub.")
    except Exception as e:
        st.error(f"Failed to push cache to GitHub: {e}")
