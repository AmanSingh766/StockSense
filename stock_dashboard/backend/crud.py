"""
CRUD — Database query functions for all API endpoints.
"""

import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
# from database import StockData
# from data_fetcher import COMPANIES
from backend.database import StockData
from backend.data_fetcher import COMPANIES

def get_companies(db: Session):
    """Return all companies with latest price and daily return."""
    result = []
    for symbol, company_name in COMPANIES.items():
        latest = (
            db.query(StockData)
            .filter(StockData.symbol == symbol)
            .order_by(desc(StockData.date))
            .first()
        )
        if latest:
            result.append({
                "symbol": symbol,
                "company_name": company_name,
                "latest_close": latest.close,
                "daily_return_pct": round(latest.daily_return * 100, 2) if latest.daily_return else None,
                "latest_date": str(latest.date),
            })
    return {"count": len(result), "companies": result}


def get_stock_data(db: Session, symbol: str, days: int = 30):
    """Return last N days of stock data for a symbol."""
    cutoff = datetime.today().date() - timedelta(days=days)
    rows = (
        db.query(StockData)
        .filter(StockData.symbol == symbol, StockData.date >= cutoff)
        .order_by(asc(StockData.date))
        .all()
    )

    return [
        {
            "date": str(r.date),
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume,
            "daily_return_pct": round(r.daily_return * 100, 2) if r.daily_return else None,
            "ma_7": r.ma_7,
            "ma_20": r.ma_20,
            "volatility": r.volatility,
        }
        for r in rows
    ]


def get_summary(db: Session, symbol: str):
    """Return 52-week high/low, avg close, volatility score, momentum."""
    latest = (
        db.query(StockData)
        .filter(StockData.symbol == symbol)
        .order_by(desc(StockData.date))
        .first()
    )
    if not latest:
        return None

    # Avg close over all stored data
    avg_close = db.query(func.avg(StockData.close)).filter(StockData.symbol == symbol).scalar()

    # Volatility score: average volatility over last 30 days
    cutoff_30 = datetime.today().date() - timedelta(days=30)
    recent = (
        db.query(StockData)
        .filter(StockData.symbol == symbol, StockData.date >= cutoff_30)
        .all()
    )
    avg_volatility = (
        np.mean([r.volatility for r in recent if r.volatility]) if recent else None
    )

    # Momentum: % change from 30 days ago to today
    oldest_recent = min(recent, key=lambda r: r.date) if recent else None
    momentum_pct = None
    if oldest_recent and oldest_recent.close:
        momentum_pct = round(((latest.close - oldest_recent.close) / oldest_recent.close) * 100, 2)

    return {
        "symbol": symbol,
        "company_name": latest.company_name,
        "latest_close": latest.close,
        "latest_date": str(latest.date),
        "week52_high": latest.week52_high,
        "week52_low": latest.week52_low,
        "avg_close": round(avg_close, 2) if avg_close else None,
        "volatility_score": round(avg_volatility * 100, 4) if avg_volatility else None,
        "momentum_30d_pct": momentum_pct,
        "ma_7": latest.ma_7,
        "ma_20": latest.ma_20,
        "daily_return_pct": round(latest.daily_return * 100, 2) if latest.daily_return else None,
    }


def compare_stocks(db: Session, symbol1: str, symbol2: str):
    """Compare two stocks' normalized performance over last 90 days."""
    cutoff = datetime.today().date() - timedelta(days=90)

    def fetch(sym):
        return (
            db.query(StockData)
            .filter(StockData.symbol == sym, StockData.date >= cutoff)
            .order_by(asc(StockData.date))
            .all()
        )

    rows1 = fetch(symbol1)
    rows2 = fetch(symbol2)

    if not rows1 or not rows2:
        return None

    def normalize(rows):
        base = rows[0].close
        return [
            {
                "date": str(r.date),
                "close": r.close,
                "normalized": round((r.close / base - 1) * 100, 4),
                "daily_return_pct": round(r.daily_return * 100, 2) if r.daily_return else None,
            }
            for r in rows
        ]

    d1 = normalize(rows1)
    d2 = normalize(rows2)

    perf1 = d1[-1]["normalized"] if d1 else 0
    perf2 = d2[-1]["normalized"] if d2 else 0

    return {
        "period": "90 days",
        symbol1: {
            "company_name": rows1[0].company_name,
            "performance_pct": perf1,
            "data": d1,
        },
        symbol2: {
            "company_name": rows2[0].company_name,
            "performance_pct": perf2,
            "data": d2,
        },
        "winner": symbol1 if perf1 > perf2 else symbol2,
        "difference_pct": round(abs(perf1 - perf2), 4),
    }


def get_top_gainers_losers(db: Session, top_n: int = 5):
    """Return top N gainers and losers by latest daily return."""
    latest_dates = {}
    for symbol in COMPANIES:
        row = (
            db.query(StockData)
            .filter(StockData.symbol == symbol)
            .order_by(desc(StockData.date))
            .first()
        )
        if row:
            latest_dates[symbol] = row

    ranked = sorted(
        latest_dates.values(),
        key=lambda r: r.daily_return if r.daily_return else 0,
        reverse=True,
    )

    def to_dict(r):
        return {
            "symbol": r.symbol,
            "company_name": r.company_name,
            "close": r.close,
            "daily_return_pct": round(r.daily_return * 100, 2) if r.daily_return else None,
            "date": str(r.date),
        }

    return {
        "top_gainers": [to_dict(r) for r in ranked[:top_n]],
        "top_losers": [to_dict(r) for r in ranked[-top_n:][::-1]],
    }


def get_correlation(db: Session, symbol1: str, symbol2: str):
    """Calculate Pearson correlation of daily returns between two stocks."""
    cutoff = datetime.today().date() - timedelta(days=90)

    def get_returns(sym):
        rows = (
            db.query(StockData)
            .filter(StockData.symbol == sym, StockData.date >= cutoff)
            .order_by(asc(StockData.date))
            .all()
        )
        return {str(r.date): r.daily_return for r in rows if r.daily_return is not None}

    r1 = get_returns(symbol1)
    r2 = get_returns(symbol2)

    # Intersect dates
    common_dates = sorted(set(r1.keys()) & set(r2.keys()))
    if len(common_dates) < 10:
        return None

    arr1 = np.array([r1[d] for d in common_dates])
    arr2 = np.array([r2[d] for d in common_dates])
    corr = np.corrcoef(arr1, arr2)[0, 1]

    interpretation = (
        "Strong positive" if corr > 0.7
        else "Moderate positive" if corr > 0.3
        else "Weak/No correlation" if corr > -0.3
        else "Moderate negative" if corr > -0.7
        else "Strong negative"
    )

    return {
        "symbol1": symbol1,
        "symbol2": symbol2,
        "correlation": round(float(corr), 4),
        "interpretation": interpretation,
        "data_points": len(common_dates),
        "period": "90 days",
    }
