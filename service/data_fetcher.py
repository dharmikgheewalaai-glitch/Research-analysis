# services/data_fetcher.py
import yfinance as yf
import pandas as pd

def fetch_from_yahoo(symbol: str, interval: str = "1d", start: str = None, end: str = None, period: str = None) -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance using yfinance.
    interval: '1d','1m','5m','15m','1h'...
    Use either start & end or period.
    Returns DataFrame indexed by datetime with columns: open, high, low, close, volume
    """
    if period is None and (start is None or end is None):
        period = "1y"
    data = yf.download(tickers=symbol, interval=interval, start=start, end=end, period=period, progress=False)
    if data.empty:
        raise ValueError(f"No data fetched for {symbol} with interval={interval}")
    df = data[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "volume"]
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df

def load_from_csv(path: str, datetime_col: str = None) -> pd.DataFrame:
    df = pd.read_csv(path)
    if datetime_col is None:
        for col in ["datetime", "date", "time"]:
            if col in df.columns:
                datetime_col = col
                break
    if datetime_col is None:
        raise ValueError("CSV must contain a datetime column (datetime/date/time)")
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df = df.set_index(datetime_col)
    df = df.rename(columns={c: c.lower() for c in df.columns})
    expected = ["open", "high", "low", "close"]
    for e in expected:
        if e not in df.columns:
            raise ValueError(f"CSV missing required column: {e}")
    if "volume" not in df.columns:
        df["volume"] = 0
    df = df[["open","high","low","close","volume"]]
    df = df.sort_index()
    return df
