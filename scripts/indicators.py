import ta
import pandas as pd

def add_indicators(df):
    # Ensure 'Close' column is numeric
    if 'Close' not in df.columns:
        raise ValueError("DataFrame does not have a 'Close' column")
    
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    df = df.dropna(subset=['Close'])
    
    # Check enough data for EMA50
    if len(df) < 50:
        raise ValueError("Not enough data to calculate EMA50. Try a longer period or shorter interval.")
    
    df['EMA50'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    
    return df
