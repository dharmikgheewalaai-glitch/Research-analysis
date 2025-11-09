import pandas as pd
import talib

def MA_Crossover(data, params):
    short_window = params["short_window"]
    long_window = params["long_window"]
    data["MA_Short"] = data["Close"].rolling(short_window).mean()
    data["MA_Long"] = data["Close"].rolling(long_window).mean()
    data["Signal"] = 0
    data.loc[data["MA_Short"] > data["MA_Long"], "Signal"] = 1
    data.loc[data["MA_Short"] < data["MA_Long"], "Signal"] = -1
    return data[["Date","Close","Signal"]]

def RSI_MA_Combo(data, params):
    rsi_period = params["rsi_period"]
    ma_period = params["ma_period"]
    data["RSI"] = talib.RSI(data["Close"], timeperiod=rsi_period)
    data["MA"] = data["Close"].rolling(ma_period).mean()
    data["Signal"] = 0
    data.loc[(data["Close"] > data["MA"]) & (data["RSI"] > 50), "Signal"] = 1
    data.loc[(data["Close"] < data["MA"]) & (data["RSI"] < 50), "Signal"] = -1
    return data[["Date","Close","Signal"]]

def BreakoutStrategy(data, params):
    lookback = params["lookback_period"]
    data["High_Max"] = data["High"].rolling(lookback).max()
    data["Low_Min"] = data["Low"].rolling(lookback).min()
    data["Signal"] = 0
    data.loc[data["Close"] > data["High_Max"].shift(1), "Signal"] = 1
    data.loc[data["Close"] < data["Low_Min"].shift(1), "Signal"] = -1
    return data[["Date","Close","Signal"]]
