"""
Data Fetcher — Downloads NSE stock data via yfinance,
cleans it with Pandas, and stores it in SQLite.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from database import SessionLocal, StockData

# Top 15 NSE stocks (Nifty blue chips)
COMPANIES = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "INFY.NS": "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "ITC.NS": "ITC Limited",
    "SBIN.NS": "State Bank of India",
    "BAJFINANCE.NS": "Bajaj Finance",
    "WIPRO.NS": "Wipro",
    "AXISBANK.NS": "Axis Bank",
    "MARUTI.NS": "Maruti Suzuki",
    "TATAMOTORS.NS": "Tata Motors",
    "SUNPHARMA.NS": "Sun Pharmaceutical",
    "ADANIENT.NS": "Adani Enterprises",
}


def fetch_and_store_all():
    """Fetch 1 year of data for all companies and store in DB.
    Falls back to realistic mock data if network is unavailable.
    """
    from mock_data import generate_mock_data

    db = SessionLocal()
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)

    for symbol, company_name in COMPANIES.items():
        df = None
        try:
            print(f"  Fetching {company_name} ({symbol})...")
            raw = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if not raw.empty:
                df = clean_and_enrich(raw, symbol, company_name)
            else:
                raise ValueError("Empty response from yfinance")
        except Exception as e:
            print(f"  ⚠ yfinance failed ({e}), using mock data for {symbol}")
            df = generate_mock_data(symbol, company_name, days=365)

        if df is None or df.empty:
            print(f"  ✗ Skipping {symbol}")
            continue

        for rec in df.to_dict(orient="records"):
            try:
                db.add(StockData(**rec))
                db.commit()
            except IntegrityError:
                db.rollback()

    db.close()
    print("✅ All data fetched and stored.")


def clean_and_enrich(df: pd.DataFrame, symbol: str, company_name: str) -> pd.DataFrame:
    """
    Clean raw yfinance DataFrame and add computed metrics:
    - Daily Return
    - 7-day & 20-day Moving Average
    - 7-day Rolling Volatility Score
    - 52-week High / Low
    """
    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "volume"]

    # Drop rows with missing close prices
    df.dropna(subset=["close"], inplace=True)

    # Fill remaining NaN with forward fill
    df.ffill(inplace=True)

    # Convert index to proper dates
    df.index = pd.to_datetime(df.index).date

    # Computed Metrics
    df["daily_return"] = ((df["close"] - df["open"]) / df["open"]).round(6)
    df["ma_7"] = df["close"].rolling(window=7).mean().round(2)
    df["ma_20"] = df["close"].rolling(window=20).mean().round(2)
    df["volatility"] = df["daily_return"].rolling(window=7).std().round(6)

    # 52-week High / Low (rolling over full year)
    df["week52_high"] = df["high"].rolling(window=252, min_periods=1).max().round(2)
    df["week52_low"] = df["low"].rolling(window=252, min_periods=1).min().round(2)

    df["symbol"] = symbol
    df["company_name"] = company_name
    df["date"] = df.index

    df.reset_index(drop=True, inplace=True)

    return df[
        [
            "symbol", "company_name", "date",
            "open", "high", "low", "close", "volume",
            "daily_return", "ma_7", "ma_20", "volatility",
            "week52_high", "week52_low",
        ]
    ]
