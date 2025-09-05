import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

st.title("Equity Stocks with Continuous Positive Change")

# Load CSV
csv_file = "All Stocks Streamlit.csv"
df_stocks = pd.read_csv(csv_file)
df_stocks.columns = df_stocks.columns.str.strip()
st.write("Sample stock list:")
st.dataframe(df_stocks.head())

# Filter only equities: ISIN starting with 'INE'
df_equity = df_stocks[df_stocks['ISIN'].str.startswith('INE')].copy()
st.write(f"Filtered equity stocks: {len(df_equity)}")
st.dataframe(df_equity.head())

# User input: consecutive positive days
n_days = st.number_input("Select number of consecutive positive days", min_value=1, max_value=7, value=3, step=1)

# Date range: today + last 7 days
end_date = datetime.today()
start_date = end_date - timedelta(days=7)

st.write("Fetching data... this may take a while.")

results = []

for idx, row in df_equity.iterrows():
    symbol = row['Code']
    exchange = row['EXCH']
    
    # Construct yfinance ticker
    if exchange.upper() == "NSE":
        ticker = f"{symbol}.NS"
    elif exchange.upper() == "BSE":
        ticker = f"{symbol}.BO"
    else:
        ticker = symbol

    try:
        # Fetch historical data
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            continue
        
        # Ensure 'Close' and 'Volume' exist
        if 'Close' not in data.columns or 'Volume' not in data.columns:
            continue
        
        # Calculate daily change
        close_prices = data['Close']
        daily_change = close_prices.diff().tail(n_days)
        
        if len(daily_change) < n_days:
            continue
        
        # Check continuous positive change
        if (daily_change > 0).all():
            last_row = data.iloc[-1]
            daily_changes_dict = daily_change.to_dict()
            results.append({
                'Symbol': symbol,
                'Exchange': exchange,
                'Last_Close': last_row['Close'],
                'Last_Volume': last_row['Volume'],
                'Daily_Change': daily_changes_dict
            })
    except Exception as e:
        st.write(f"Skipped {ticker}: {e}")
        continue

# Display results
if results:
    st.success(f"Found {len(results)} equity stocks with continuous positive change for {n_days} days.")
    st.dataframe(pd.DataFrame(results))
else:
    st.warning(f"No equity stocks found with continuous positive change for {n_days} days.")
