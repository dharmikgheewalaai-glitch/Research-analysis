# strategy/strategies.py
import pandas as pd
import numpy as np

class MA_Crossover:
    def __init__(self, fast=7, slow=21):
        assert fast < slow, "fast must be smaller than slow"
        self.fast = fast
        self.slow = slow

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["ma_fast"] = df["close"].rolling(self.fast).mean()
        df["ma_slow"] = df["close"].rolling(self.slow).mean()
        df["signal"] = 0
        df.loc[df["ma_fast"] > df["ma_slow"], "signal"] = 1
        df.loc[df["ma_fast"] < df["ma_slow"], "signal"] = -1
        df["signal_change"] = df["signal"].diff().fillna(0)
        df["trade_signal"] = df["signal_change"].apply(lambda x: "BUY" if x > 0 else ("SELL" if x < 0 else None))
        return df

    def last_signal(self, df: pd.DataFrame):
        if df.empty: return None
        return df["trade_signal"].iloc[-1]

class RSI_MA_Combo:
    def __init__(self, fast=7, slow=21, rsi_window=14):
        self.fast = fast
        self.slow = slow
        self.rsi_window = rsi_window

    def _rsi(self, series: pd.Series, window: int=14):
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -1*delta.clip(upper=0)
        ma_up = up.ewm(alpha=1/window, adjust=False).mean()
        ma_down = down.ewm(alpha=1/window, adjust=False).mean()
        rs = ma_up / (ma_down + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["ma_fast"] = df["close"].rolling(self.fast).mean()
        df["ma_slow"] = df["close"].rolling(self.slow).mean()
        df["rsi"] = self._rsi(df["close"], self.rsi_window)
        # signal: buy when rsi > 50 and ma_fast > ma_slow; sell when rsi < 50 and ma_fast < ma_slow
        df["trade_signal"] = None
        cond_buy = (df["rsi"] > 50) & (df["ma_fast"] > df["ma_slow"])
        cond_sell = (df["rsi"] < 50) & (df["ma_fast"] < df["ma_slow"])
        # mark only crossovers: detect change in cond
        df["cond"] = 0
        df.loc[cond_buy, "cond"] = 1
        df.loc[cond_sell, "cond"] = -1
        df["cond_change"] = df["cond"].diff().fillna(0)
        df.loc[df["cond_change"] > 0, "trade_signal"] = "BUY"
        df.loc[df["cond_change"] < 0, "trade_signal"] = "SELL"
        return df

    def last_signal(self, df: pd.DataFrame):
        if df.empty: return None
        return df["trade_signal"].iloc[-1]

class BreakoutStrategy:
    def __init__(self, n=20):
        self.n = n

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["n_high"] = df["high"].rolling(self.n).max().shift(1)
        df["n_low"] = df["low"].rolling(self.n).min().shift(1)
        df["trade_signal"] = None
        df.loc[df["close"] > df["n_high"], "trade_signal"] = "BUY"
        df.loc[df["close"] < df["n_low"], "trade_signal"] = "SELL"
        # keep only first breakout until reversal: detect changes
        df["trade_signal"] = df["trade_signal"].where(df["trade_signal"] != df["trade_signal"].shift(1))
        return df

    def last_signal(self, df: pd.DataFrame):
        if df.empty: return None
        return df["trade_signal"].iloc[-1]
