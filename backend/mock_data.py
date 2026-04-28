"""
Mock Data Generator — Generates realistic-looking NSE stock data
when yfinance is unavailable (e.g., network restrictions).
Uses numpy random walk to simulate prices.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Realistic base prices for NSE stocks
BASE_PRICES = {
    "RELIANCE.NS": 2850.0,
    "TCS.NS": 3950.0,
    "INFY.NS": 1780.0,
    "HDFCBANK.NS": 1640.0,
    "ICICIBANK.NS": 1220.0,
    "HINDUNILVR.NS": 2380.0,
    "ITC.NS": 475.0,
    "SBIN.NS": 820.0,
    "BAJFINANCE.NS": 6900.0,
    "WIPRO.NS": 530.0,
    "AXISBANK.NS": 1150.0,
    "MARUTI.NS": 12800.0,
    "TATAMOTORS.NS": 950.0,
    "SUNPHARMA.NS": 1750.0,
    "ADANIENT.NS": 2400.0,
}


def generate_mock_data(symbol: str, company_name: str, days: int = 365) -> pd.DataFrame:
    """
    Generate a realistic stock price DataFrame using a geometric random walk.
    """
    np.random.seed(hash(symbol) % (2**31))  # Deterministic per symbol

    base_price = BASE_PRICES.get(symbol, 1000.0)
    end_date = datetime.today().date()
    # Generate dates (skip weekends)
    all_dates = pd.bdate_range(end=end_date, periods=days)

    n = len(all_dates)

    # Simulate daily log returns: slight upward drift + volatility
    mu = 0.0003       # ~7.5% annual drift
    sigma = 0.015     # ~1.5% daily volatility
    log_returns = np.random.normal(mu, sigma, n)
    prices = base_price * np.exp(np.cumsum(log_returns))

    # Simulate OHLCV from close prices
    noise_h = np.abs(np.random.normal(0, 0.008, n))  # daily high spread
    noise_l = np.abs(np.random.normal(0, 0.008, n))  # daily low spread
    noise_o = np.random.normal(0, 0.005, n)           # open vs close gap

    closes = prices
    opens  = closes * (1 + noise_o)
    highs  = np.maximum(closes, opens) * (1 + noise_h)
    lows   = np.minimum(closes, opens) * (1 - noise_l)
    volumes = np.random.randint(500_000, 5_000_000, n).astype(float)

    df = pd.DataFrame({
        "date": all_dates.date,
        "open": np.round(opens, 2),
        "high": np.round(highs, 2),
        "low": np.round(lows, 2),
        "close": np.round(closes, 2),
        "volume": volumes,
    })

    # Calculated metrics
    df["daily_return"] = ((df["close"] - df["open"]) / df["open"]).round(6)
    df["ma_7"]  = df["close"].rolling(7).mean().round(2)
    df["ma_20"] = df["close"].rolling(20).mean().round(2)
    df["volatility"] = df["daily_return"].rolling(7).std().round(6)
    df["week52_high"] = df["high"].rolling(252, min_periods=1).max().round(2)
    df["week52_low"]  = df["low"].rolling(252, min_periods=1).min().round(2)
    df["symbol"] = symbol
    df["company_name"] = company_name

    return df[[
        "symbol", "company_name", "date",
        "open", "high", "low", "close", "volume",
        "daily_return", "ma_7", "ma_20", "volatility",
        "week52_high", "week52_low",
    ]]
