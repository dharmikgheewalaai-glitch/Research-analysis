# Non-Automated Trading Analysis (Multi-Strategy)

This repository provides a **non-automated** Streamlit dashboard and a backtesting script.
It supports three strategies:
- Moving Average Crossover
- RSI + Moving Average Combo
- Breakout (N-day high/low)

Data sources:
- Yahoo Finance (via `yfinance`)
- CSV upload (columns: datetime, open, high, low, close, volume)

**Important:** This project will NOT place live orders. It is for analysis and manual decision support only.

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
