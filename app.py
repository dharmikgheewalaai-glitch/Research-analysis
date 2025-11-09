
# app.py
import streamlit as st
import pandas as pd
import yaml
from services.data_fetcher import fetch_from_yahoo, load_from_csv
from strategy.strategies import MA_Crossover, RSI_MA_Combo, BreakoutStrategy
from services.order_manager import OrderManager
import plotly.graph_objects as go
import vectorbt as vbt
from datetime import datetime

st.set_page_config(layout="wide", page_title="Trading Analysis Dashboard")

# Load config
with open("config.yaml") as f:
    cfg = yaml.safe_load(f)

DEFAULT = cfg["default"]
STRAT_CFG = cfg["strategy"]

# Order manager (manual logger)
om = OrderManager(path=cfg.get("order_log", "data/trades.csv"))

st.title("📊 Non-Automated Trading Analysis (Multi-Strategy)")

# Sidebar - Data source
st.sidebar.header("Data Source & Range")
data_source = st.sidebar.selectbox("Choose data source", ["Yahoo Finance", "Upload CSV"])
if data_source == "Yahoo Finance":
    symbol = st.sidebar.text_input("Symbol", DEFAULT["symbol"])
    interval = st.sidebar.selectbox("Interval", ["1d", "1h", "30m", "15m", "5m", "1m"], index=0)
    start = st.sidebar.date_input("Start date", pd.to_datetime(DEFAULT["start"]).date())
    end = st.sidebar.date_input("End date", pd.to_datetime(DEFAULT["end"]).date())
else:
    uploaded_file = st.sidebar.file_uploader("Upload OHLC CSV", type=["csv"])

# Sidebar - Strategy selection
st.sidebar.header("Strategy")
strategy_name = st.sidebar.selectbox("Strategy", ["MA Crossover", "RSI + MA Combo", "Breakout"])
# strategy params (defaults from config)
fast = st.sidebar.number_input("Fast MA", value=STRAT_CFG["fast_ma"], min_value=1)
slow = st.sidebar.number_input("Slow MA", value=STRAT_CFG["slow_ma"], min_value=2)
rsi_window = st.sidebar.number_input("RSI Window", value=STRAT_CFG["rsi_window"], min_value=2)
breakout_n = st.sidebar.number_input("Breakout N days", value=STRAT_CFG["breakout_n"], min_value=1)

# Sidebar - Manual trade logger
st.sidebar.header("Manual Trade Logger (No Automation)")
manual_symbol = st.sidebar.text_input("Trade Symbol", DEFAULT["symbol"], key="manual_symbol")
side = st.sidebar.radio("Side", ["BUY", "SELL"], key="manual_side")
qty = st.sidebar.number_input("Quantity", value=1, min_value=1, key="manual_qty")
entry_price = st.sidebar.number_input("Entry Price", value=0.0, format="%.2f", key="manual_entry")
exit_price = st.sidebar.number_input("Exit Price (optional)", value=0.0, format="%.2f", key="manual_exit")
notes = st.sidebar.text_input("Notes", key="manual_notes")
if st.sidebar.button("Log Trade"):
    if entry_price <= 0:
        st.sidebar.error("Entry price must be > 0")
    else:
        pnl = None
        if exit_price and exit_price > 0:
            pnl = (exit_price - entry_price) * qty if side == "BUY" else (entry_price - exit_price) * qty
        om.log_trade(manual_symbol, side, qty, entry_price, exit_price if exit_price>0 else None, pnl, notes)
        st.sidebar.success("Trade logged")

# Load data
with st.spinner("Loading data..."):
    try:
        if data_source == "Yahoo Finance":
            df = fetch_from_yahoo(symbol, interval=interval, start=str(start), end=str(end))
            display_symbol = symbol
        else:
            if uploaded_file is None:
                st.warning("Upload a CSV to proceed.")
                st.stop()
            df = load_from_csv(uploaded_file)
            display_symbol = "Uploaded CSV"
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        st.stop()

if df.empty:
    st.error("No data available.")
    st.stop()

# Choose strategy object
if strategy_name == "MA Crossover":
    strat = MA_Crossover(fast=fast, slow=slow)
elif strategy_name == "RSI + MA Combo":
    strat = RSI_MA_Combo(fast=fast, slow=slow, rsi_window=rsi_window)
else:
    strat = BreakoutStrategy(n=breakout_n)

# Prepare signals
df_ind = strat.prepare(df)
last_signal = strat.last_signal(df_ind)

# Layout
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader(f"{display_symbol} — {strategy_name}")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df_ind.index,
                                 open=df_ind["open"],
                                 high=df_ind["high"],
                                 low=df_ind["low"],
                                 close=df_ind["close"],
                                 name="OHLC"))
    if "ma_fast" in df_ind.columns:
        fig.add_trace(go.Scatter(x=df_ind.index, y=df_ind["ma_fast"], name=f"MA {fast}"))
    if "ma_slow" in df_ind.columns:
        fig.add_trace(go.Scatter(x=df_ind.index, y=df_ind["ma_slow"], name=f"MA {slow}"))
    # signals
    buys = df_ind[df_ind["trade_signal"] == "BUY"]
    sells = df_ind[df_ind["trade_signal"] == "SELL"]
    if not buys.empty:
        fig.add_trace(go.Scatter(x=buys.index, y=buys["close"], mode="markers", marker_symbol="triangle-up", marker_size=10, name="BUY"))
    if not sells.empty:
        fig.add_trace(go.Scatter(x=sells.index, y=sells["close"], mode="markers", marker_symbol="triangle-down", marker_size=10, name="SELL"))
    fig.update_layout(height=650, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.metric("Last Close", f"{df_ind['close'].iloc[-1]:.2f}")
    st.metric("Current Signal", last_signal or "HOLD")
    st.markdown("**Recent Values**")
    st.table(df_ind[['close'] + [c for c in ['ma_fast','ma_slow','rsi','vol_at_price'] if c in df_ind.columns]].tail(5))

# Quick backtest using vectorbt
st.header("Quick Backtest Summary")
try:
    close = df_ind["close"]
    # Entries/exits derived from strategy signals (True/False)
    entries = df_ind["ma_fast"] > df_ind["ma_slow"] if "ma_fast" in df_ind.columns else pd.Series(False, index=close.index)
    exits = df_ind["ma_fast"] < df_ind["ma_slow"] if "ma_fast" in df_ind.columns else pd.Series(False, index=close.index)

    # For RSI combo and breakout we try produce entries/exits via trade_signal (simple)
    entries = df_ind["trade_signal"] == "BUY"
    exits = df_ind["trade_signal"] == "SELL"

    pf = vbt.Portfolio.from_signals(close, entries, exits, init_cash=100000, fees=0.0005, freq=interval if isinstance(interval, str) else "1d")
    stats = pf.stats()
    # Select key metrics
    metrics = {
        "Total Return (%)": stats.get("Total Return [%]") if "Total Return [%]" in stats.index else pf.total_return()*100,
        "Annualized Return (%)": stats.get("Annualized Return [%]") if "Annualized Return [%]" in stats.index else None,
        "Sharpe Ratio": stats.get("Sharpe Ratio"),
        "Max Drawdown (%)": stats.get("Max Drawdown [%]") if "Max Drawdown [%]" in stats.index else pf.max_drawdown()*100,
        "Win Rate (%)": stats.get("Win Rate [%]") if "Win Rate [%]" in stats.index else (pf.trades.win_rate() * 100 if pf.trades.records_readable else None),
        "Total Trades": stats.get("Total Trades") if "Total Trades" in stats.index else pf.total_trades
    }
    st.write("Selected metrics:")
    st.json({k: float(v) if v is not None else None for k, v in metrics.items()})
    st.subheader("Equity Curve")
    st.line_chart(pf.value())
except Exception as e:
    st.info("vectorbt quick backtest not available or failed: run backtest.py for a full report.")
    st.write(e)

# Manual trade log
st.header("Manual Trade Log")
trades_df = om.read_trades()
st.dataframe(trades_df.sort_values("timestamp", ascending=False))

st.markdown("---")
st.markdown("**Notes:** This dashboard **does not** place or automate trades. Use it for analysis and manual decision-making.")
