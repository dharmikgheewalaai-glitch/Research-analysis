import yfinance as yf
import pandas as pd

def fetch_from_yahoo(symbol, interval="1d"):
    data = yf.download(symbol, period="6mo", interval=interval)
    data.reset_index(inplace=True)
    return data

def load_from_csv(file_path):
    return pd.read_csv(file_path)
