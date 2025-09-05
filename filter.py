import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# ---------------------------
# Streamlit App
# ---------------------------
st.title("Stocks with Continuous Positive Change")

# CSV path in the same folder (replace with actual filename)
csv_file = "All Stocks Streamlit.csv"
df_stocks = pd.read_csv(csv_file)

st.write("Sample of stock list from CSV:")
st.dataframe(df_stocks.head())

# User input: number of consecutive positive days
n_days = st.number_input("Select number of consecutive positive days", min_value=1, max_value=7, value=3, step=1)

# Date range: today and last 7 days
end_date = datetime.today()
start_date = end_date - timedelta(days=7)

st.write("Fetching data, please wait...")

results = []

# Loop through each stock
for idx, row in df_stocks.iterrows():
    symbol = row['b']  # Column 'b' has stock code
    exchange = row['e']  # Column 'e' has exchange code
    
    # Construct yfinance ticker
    if exchange.upper() == "NSE":
        ticker = f"{symbol}.NS"
    elif exchange.upper() == "BSE":
        ticker = f"{symbol}.BO"
    else:
        ticker = symbol
    
    try:
        # Fetch historical data
        data = yf.download(ticker, start=start_date, end=end_date)
        if data.empty or len(data) < n_days:
            continue

        # Calculate daily price change
        data['Daily_Change'] = data['Close'].diff()
        last_n_days = data['Daily_Change'].tail(n_days)
        
        if (last_n_days > 0).all():
            last_row = data.iloc[-1]
            # Save results with daily changes by date
            daily_changes = last_n_days.to_dict()
            results.append({
                'Symbol': symbol,
                'Exchange': exchange,
                'Last_Close': last_row['Close'],
                'Last_Volume': last_row['Volume'],
                'Daily_Change': daily_changes
            })
    except Exception as e:
        st.write(f"Error fetching {ticker}: {e}")
        continue

# Display results
if results:
    st.success(f"Found {len(results)} stocks with continuous positive change for {n_days} days.")
    st.dataframe(pd.DataFrame(results))
else:
    st.warning(f"No stocks found with continuous positive change for {n_days} days.")
