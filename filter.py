import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# ---------------------------
# Load stock list
# ---------------------------
st.title("Continuous Positive Change Stocks Filter")

uploaded_file = st.file_uploader("Upload 'All Stocks Streamlit.csv'", type=["csv"])

if uploaded_file:
    df_stocks = pd.read_csv(uploaded_file)
    st.write("Sample of uploaded stock list:")
    st.dataframe(df_stocks.head())

    # User input: number of consecutive positive days
    n_days = st.number_input("Select number of consecutive positive days", min_value=1, max_value=10, value=3, step=1)
    
    # Date range for fetching historical data
    end_date = datetime.today()
    start_date = end_date - timedelta(days=20)  # extra days to ensure we cover n_days
    
    st.write("Fetching data, please wait...")
    
    results = []

    # Loop through each stock
    for idx, row in df_stocks.iterrows():
        symbol = row['b']  # assuming column b has stock code
        exchange = row['e']  # assuming column e has exchange code
        
        # Construct ticker for yfinance
        if exchange.upper() == "NSE":
            ticker = f"{symbol}.NS"
        elif exchange.upper() == "BSE":
            ticker = f"{symbol}.BO"
        else:
            ticker = symbol  # fallback
        
        try:
            # Fetch historical data
            data = yf.download(ticker, start=start_date, end=end_date)
            if data.empty:
                continue

            # Check for continuous positive change in 'Close'
            data['Daily_Change'] = data['Close'].diff()
            last_n_days = data['Daily_Change'].tail(n_days)
            
            if (last_n_days > 0).all():
                last_row = data.iloc[-1]
                results.append({
                    'Symbol': symbol,
                    'Exchange': exchange,
                    'Last_Close': last_row['Close'],
                    'Last_Volume': last_row['Volume']
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
