import os
import sys
import streamlit as st
import pandas as pd
from datetime import datetime
import yaml

# =====================
# Set project root for imports
# =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from services.data_fetcher import fetch_from_yahoo, load_from_csv
from strategy.strategies import MA_Crossover, RSI_MA_Combo, BreakoutStrategy

# =====================
# File paths
# =====================
CONFIG_FILE = os.path.join(BASE_DIR, "config.yaml")
TRADES_FILE = os.path.join(BASE_DIR, "data", "trades.csv")

# Load config
with open(CONFIG_FILE, "r") as f:
    config = yaml.safe_load(f)

symbol = config["symbol"]
interval = config["interval"]
refresh_seconds = config["refresh_seconds"]

st.title("📊 Trading Analysis Dashboard")

# Load historical data
data = fetch_from_yahoo(symbol, interval)

# Strategy selection
strategy_option = st.selectbox(
    "Select Strategy", ["MA Crossover", "RSI + MA", "Breakout"]
)

# Run strategy
if strategy_option == "MA Crossover":
    signals = MA_Crossover(data, config["strategies"]["ma_crossover"])
elif strategy_option == "RSI + MA":
    signals = RSI_MA_Combo(data, config["strategies"]["rsi_ma"])
elif strategy_option == "Breakout":
    signals = BreakoutStrategy(data, config["strategies"]["breakout"])

# Display signals
st.subheader("Signals")
st.dataframe(signals.tail(10))

# Save signals to CSV (paper trading log)
signals["date_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
signals.to_csv(TRADES_FILE, mode="a", header=False, index=False)

st.success(f"Signals logged to {TRADES_FILE}")
