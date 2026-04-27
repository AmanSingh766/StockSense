import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import engine, SessionLocal, StockData, CompanyInfo, init_db

# Indian NSE stocks + some popular ones
COMPANIES = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "INFY.NS": "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
    "WIPRO.NS": "Wipro",
    "BAJFINANCE.NS": "Bajaj Finance",
    "SBIN.NS": "State Bank of India",
    "ADANIENT.NS": "Adani Enterprises",
    "TATAMOTORS.NS": "Tata Motors",
}


def fetch_and_store(symbol: str, company_name: str, db: Session):
    try:
        ticker = yf.Ticker(symbol)
        end = datetime.today()
        start = end - timedelta(days=380)  # ~52 weeks + buffer

        df = ticker.history(start=start, end=end)
        if df.empty:
            print(f"  No data for {symbol}, skipping.")
            return

        info = ticker.info

        # Upsert company info
        existing = db.query(CompanyInfo).filter(CompanyInfo.symbol == symbol).first()
        if not existing:
            ci = CompanyInfo(
                symbol=symbol,
                company_name=company_name,
                sector=info.get("sector", "N/A"),
                industry=info.get("industry", "N/A"),
                market_cap=info.get("marketCap", 0),
                description=info.get("longBusinessSummary", "")[:500] if info.get("longBusinessSummary") else "",
            )
            db.add(ci)

        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        df["date"] = pd.to_datetime(df["date"]).dt.date

        # Handle missing values
        df = df.dropna(subset=["open", "high", "low", "close"])
        df["volume"] = df["volume"].fillna(0)

        # Calculated metrics
        df["daily_return"] = (df["close"] - df["open"]) / df["open"] * 100
        df["ma_7"] = df["close"].rolling(window=7, min_periods=1).mean()

        # Delete old data and re-insert
        db.query(StockData).filter(StockData.symbol == symbol).delete()

        for _, row in df.iterrows():
            sd = StockData(
                symbol=symbol,
                company_name=company_name,
                date=row["date"],
                open=round(float(row["open"]), 2),
                high=round(float(row["high"]), 2),
                low=round(float(row["low"]), 2),
                close=round(float(row["close"]), 2),
                volume=float(row["volume"]),
                daily_return=round(float(row["daily_return"]), 4),
                ma_7=round(float(row["ma_7"]), 2),
            )
            db.add(sd)

        db.commit()
        print(f"  ✅ {symbol}: {len(df)} rows stored")

    except Exception as e:
        db.rollback()
        print(f"  ❌ Error for {symbol}: {e}")


def run_ingestion():
    init_db()
    db = SessionLocal()
    print("📥 Starting data ingestion...")
    for symbol, name in COMPANIES.items():
        print(f"  Fetching {name} ({symbol})...")
        fetch_and_store(symbol, name, db)
    db.close()
    print("✅ Data ingestion complete!")


if __name__ == "__main__":
    run_ingestion()
