import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

st.title("Stocks with Continuous Positive Change (Fast)")

# Load CSV
csv_file = "Github_Stocks.csv"
df_stocks = pd.read_csv(csv_file)
df_stocks.columns = df_stocks.columns.str.strip()
st.write("Sample stock list:")
st.dataframe(df_stocks.head())

# User input: consecutive positive days
n_days = st.number_input(
    "Select number of consecutive positive days",
    min_value=1,
    max_value=7,
    value=3,
    step=1
)

# Filter only rows with non-empty Symbol3
df_stocks = df_stocks[df_stocks['Symbol3'].notnull()].copy()
st.write(f"Total stocks to fetch: {len(df_stocks)}")

# Prepare tickers for yfinance
tickers = []
ticker_map = {}  # Map ticker to original symbol & exchange info if available
for idx, row in df_stocks.iterrows():
    symbol = row['Symbol3'].strip()
    # If you have an Exchange column, you can append .NS or .BO; otherwise assume NSE
    ticker = f"{symbol}.NS"  # default NSE; change if you have exchange info
    tickers.append(ticker)
    ticker_map[ticker] = {'Symbol3': symbol}

# Date range: today + last 7 days
end_date = datetime.today()
start_date = end_date - timedelta(days=7)

st.write("Fetching data for all stocks at once...")

try:
    # Fetch all tickers together
    data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', progress=False)
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

results = []

for ticker in tickers:
    try:
        # Handle single vs multi-level columns
        if isinstance(data.columns, pd.MultiIndex):
            df = data[ticker]
        else:
            df = data
        if df.empty or 'Close' not in df.columns or 'Volume' not in df.columns:
            continue

        close_prices = df['Close']
        if len(close_prices) < n_days:
            continue

        daily_change = close_prices.diff().tail(n_days)
        if (daily_change > 0).all():
            last_row = df.iloc[-1]
            results.append({
                'Symbol3': ticker_map[ticker]['Symbol3'],
                'Last_Close': last_row['Close'],
                'Last_Volume': last_row['Volume'],
                'Daily_Change': daily_change.to_dict()
            })
    except Exception as e:
        st.write(f"Skipped {ticker}: {e}")
        continue

# Display results
if results:
    st.success(f"Found {len(results)} stocks with continuous positive change for {n_days} days.")
    st.dataframe(pd.DataFrame(results))
else:
    st.warning(f"No stocks found with continuous positive change for {n_days} days.")
