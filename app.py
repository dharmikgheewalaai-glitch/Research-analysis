import streamlit as st
import plotly.express as px
from scripts.data_fetch import fetch_data
from scripts.indicators import add_indicators
from scripts.strategy import generate_signals
from scripts.backtest import backtest

st.title("📊 Research Bot for Long Trades")

symbol = st.text_input("Enter Symbol", "^NSEI")
period = st.selectbox("Select Period", ["1mo","3mo","6mo","1y"])
interval = st.selectbox("Select Interval", ["15m","1h","1d"])  # safer intervals

if st.button("Run Analysis"):
    try:
        df = fetch_data(symbol, period, interval)
        df = add_indicators(df)
        df = generate_signals(df)
        df = backtest(df)
        
        st.subheader("Trade Signals")
        st.dataframe(df[['Datetime','Close','EMA50','RSI','Signal','Position']].tail(20))
        
        st.subheader("Cumulative Returns")
        fig = px.line(df, x='Datetime', y='Cumulative', title="Strategy Performance")
        st.plotly_chart(fig)
        
        st.subheader("Download Data")
        csv = df.to_csv(index=False).encode()
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"{symbol.replace('^','')}_analysis.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()
