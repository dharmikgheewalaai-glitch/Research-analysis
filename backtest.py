# backtest.py
import argparse
from services.data_fetcher import fetch_from_yahoo, load_from_csv
from strategy.strategies import MA_Crossover, RSI_MA_Combo, BreakoutStrategy
import vectorbt as vbt
import os
import pandas as pd

os.makedirs("results", exist_ok=True)

def run_backtest(df, strategy_name, params):
    # Prepare strategy
    if strategy_name == "ma":
        strat = MA_Crossover(fast=params.get("fast",7), slow=params.get("slow",21))
    elif strategy_name == "rsi_ma":
        strat = RSI_MA_Combo(fast=params.get("fast",7), slow=params.get("slow",21), rsi_window=params.get("rsi",14))
    else:
        strat = BreakoutStrategy(n=params.get("n",20))

    df_ind = strat.prepare(df)
    close = df_ind["close"]

    entries = df_ind["trade_signal"] == "BUY"
    exits = df_ind["trade_signal"] == "SELL"

    pf = vbt.Portfolio.from_signals(close, entries, exits, init_cash=100000, fees=0.0005)
    stats = pf.stats()
    # Save equity curve
    try:
        fig = pf.value().vbt.plot().figure
        fig.savefig(f"results/portfolio_{strategy_name}.png")
    except Exception:
        pass
    return pf, stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", type=str, default="RELIANCE.NS")
    parser.add_argument("--start", type=str, default="2020-01-01")
    parser.add_argument("--end", type=str, default="2024-12-31")
    parser.add_argument("--interval", type=str, default="1d")
    parser.add_argument("--csv", type=str, default=None)
    parser.add_argument("--strategy", type=str, default="ma", choices=["ma", "rsi_ma", "breakout"])
    parser.add_argument("--fast", type=int, default=7)
    parser.add_argument("--slow", type=int, default=21)
    parser.add_argument("--rsi", type=int, default=14)
    parser.add_argument("--n", type=int, default=20)
    args = parser.parse_args()

    if args.csv:
        df = load_from_csv(args.csv)
    else:
        df = fetch_from_yahoo(args.symbol, interval=args.interval, start=args.start, end=args.end)

    params = {"fast": args.fast, "slow": args.slow, "rsi": args.rsi, "n": args.n}
    pf, stats = run_backtest(df, args.strategy, params)
    print(stats)
    print("Saved results (if plotting supported) to /results")
