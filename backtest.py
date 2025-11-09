import os
import sys
import pandas as pd
import yaml

# =====================
# Set project root for imports
# =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from strategy.strategies import MA_Crossover, RSI_MA_Combo, BreakoutStrategy

# File paths
CONFIG_FILE = os.path.join(BASE_DIR, "config.yaml")
SAMPLE_DATA_FILE = os.path.join(BASE_DIR, "data", "sample_data.csv")

# Load config
with open(CONFIG_FILE, "r") as f:
    config = yaml.safe_load(f)

def run_backtest(strategy_name, data, config):
    if strategy_name == "MA Crossover":
        return MA_Crossover(data, config["ma_crossover"])
    elif strategy_name == "RSI + MA":
        return RSI_MA_Combo(data, config["rsi_ma"])
    elif strategy_name == "Breakout":
        return BreakoutStrategy(data, config["breakout"])
    else:
        raise ValueError("Unknown strategy")

if __name__ == "__main__":
    data = pd.read_csv(SAMPLE_DATA_FILE)
    result = run_backtest("MA Crossover", data, config["strategies"])
    print(result.tail())
