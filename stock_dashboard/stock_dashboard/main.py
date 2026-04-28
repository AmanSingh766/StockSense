"""
Stock Data Intelligence Dashboard
==================================
FastAPI Backend for Indian Stock Market Analytics
Author: Jarnox Internship Assignment
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import sqlite3
import math
import os

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="📈 Stock Data Intelligence Dashboard",
    description="""
## Jarnox Internship Assignment — Stock Data Intelligence Dashboard

A mini financial data platform built with FastAPI, SQLite, and Chart.js.

### Features
- 📊 Real-time stock data visualization
- 🔍 52-week High/Low & Moving Averages
- ⚖️ Side-by-side company comparison
- 🔥 Top Gainers & Losers
- 📉 Volatility scoring
- 🤝 Stock correlation analysis

### Indian NSE Stocks Covered
RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, WIPRO, BAJFINANCE, SBIN, ADANIENT, TATAMOTORS
    """,
    version="1.0.0",
    contact={"name": "Jarnox Internship", "email": "support@jarnox.com"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), "stock_data.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── Serve static & dashboard ─────────────────────────────────────────────────

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    index = os.path.join(static_dir, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return HTMLResponse("<h1>Stock Dashboard API</h1><p>Visit <a href='/docs'>/docs</a></p>")


# ─── API Endpoints ─────────────────────────────────────────────────────────────

@app.get("/companies", tags=["Core"], summary="List all available companies")
def get_companies():
    """Returns all companies available in the database with sector and market cap info."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT symbol, company_name, sector, industry, market_cap FROM company_info ORDER BY company_name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/data/{symbol}", tags=["Core"], summary="Get stock OHLCV data")
def get_stock_data(
    symbol: str,
    days: int = Query(30, ge=7, le=365, description="Number of days of data to return"),
):
    """
    Returns historical OHLCV data with calculated metrics for a given stock symbol.

    - **symbol**: NSE symbol (e.g. `TCS.NS`)
    - **days**: Number of trading days to return (default 30, max 365)
    """
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT date, open, high, low, close, volume, daily_return, ma_7
        FROM stock_data
        WHERE symbol = ?
        ORDER BY date DESC
        LIMIT ?
        """,
        (symbol.upper(), days),
    ).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")
    result = [dict(r) for r in rows]
    result.reverse()  # chronological order
    return {"symbol": symbol.upper(), "days": days, "count": len(result), "data": result}


@app.get("/summary/{symbol}", tags=["Core"], summary="Get 52-week summary stats")
def get_summary(symbol: str):
    """
    Returns key statistics for a stock:
    - 52-week High and Low
    - Average closing price
    - Volatility score (std deviation of daily returns)
    - Latest daily return
    - 7-day moving average (latest)
    """
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT close, daily_return, ma_7, date
        FROM stock_data
        WHERE symbol = ?
        ORDER BY date DESC
        LIMIT 252
        """,
        (symbol.upper(),),
    ).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")

    closes = [r["close"] for r in rows]
    returns = [r["daily_return"] for r in rows]

    avg = sum(closes) / len(closes)
    variance = sum((x - avg) ** 2 for x in closes) / len(closes)
    std_dev = math.sqrt(variance)

    ret_avg = sum(returns) / len(returns)
    ret_variance = sum((x - ret_avg) ** 2 for x in returns) / len(returns)
    volatility = round(math.sqrt(ret_variance), 4)

    # Volatility label
    if volatility < 1.0:
        vol_label = "Low 🟢"
    elif volatility < 2.0:
        vol_label = "Medium 🟡"
    else:
        vol_label = "High 🔴"

    return {
        "symbol": symbol.upper(),
        "52_week_high": round(max(closes), 2),
        "52_week_low": round(min(closes), 2),
        "avg_close": round(avg, 2),
        "std_deviation": round(std_dev, 2),
        "volatility_score": volatility,
        "volatility_label": vol_label,
        "latest_close": closes[0],
        "latest_return_pct": round(rows[0]["daily_return"], 4),
        "latest_ma7": round(rows[0]["ma_7"], 2),
        "data_points": len(rows),
    }


@app.get("/compare", tags=["Core"], summary="Compare two stocks")
def compare_stocks(
    symbol1: str = Query(..., example="TCS.NS"),
    symbol2: str = Query(..., example="INFY.NS"),
    days: int = Query(30, ge=7, le=365),
):
    """
    Compare performance of two stocks side-by-side.

    Returns normalized price (base 100), correlation coefficient, and % return comparison.
    """
    conn = get_conn()

    def fetch(sym):
        return conn.execute(
            """
            SELECT date, close, daily_return
            FROM stock_data WHERE symbol = ?
            ORDER BY date DESC LIMIT ?
            """,
            (sym.upper(), days),
        ).fetchall()

    rows1 = fetch(symbol1)
    rows2 = fetch(symbol2)
    conn.close()

    if not rows1:
        raise HTTPException(status_code=404, detail=f"Symbol not found: {symbol1}")
    if not rows2:
        raise HTTPException(status_code=404, detail=f"Symbol not found: {symbol2}")

    rows1 = list(reversed(rows1))
    rows2 = list(reversed(rows2))

    # Match dates
    dates1 = {r["date"]: r["close"] for r in rows1}
    dates2 = {r["date"]: r["close"] for r in rows2}
    common = sorted(set(dates1) & set(dates2))

    if not common:
        raise HTTPException(status_code=400, detail="No overlapping dates found")

    c1 = [dates1[d] for d in common]
    c2 = [dates2[d] for d in common]

    # Normalize to base 100
    n1 = [round(p / c1[0] * 100, 2) for p in c1]
    n2 = [round(p / c2[0] * 100, 2) for p in c2]

    # Pearson correlation
    n = len(c1)
    mean1, mean2 = sum(c1) / n, sum(c2) / n
    num = sum((c1[i] - mean1) * (c2[i] - mean2) for i in range(n))
    den = math.sqrt(
        sum((c1[i] - mean1) ** 2 for i in range(n)) *
        sum((c2[i] - mean2) ** 2 for i in range(n))
    )
    corr = round(num / den, 4) if den != 0 else 0

    return {
        "symbol1": symbol1.upper(),
        "symbol2": symbol2.upper(),
        "correlation": corr,
        "correlation_label": (
            "Strong Positive" if corr > 0.7
            else "Moderate Positive" if corr > 0.3
            else "Weak/No Correlation" if corr > -0.3
            else "Negative Correlation"
        ),
        "return_pct": {
            symbol1.upper(): round((c1[-1] - c1[0]) / c1[0] * 100, 2),
            symbol2.upper(): round((c2[-1] - c2[0]) / c2[0] * 100, 2),
        },
        "dates": common,
        "normalized": {
            symbol1.upper(): n1,
            symbol2.upper(): n2,
        },
        "data_points": len(common),
    }


@app.get("/gainers-losers", tags=["Insights"], summary="Top gainers and losers today")
def gainers_losers(top_n: int = Query(5, ge=1, le=10)):
    """Returns the top N gainers and losers based on latest day's daily return."""
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT s.symbol, s.company_name, s.daily_return, s.close, s.date
        FROM stock_data s
        INNER JOIN (
            SELECT symbol, MAX(date) as max_date FROM stock_data GROUP BY symbol
        ) latest ON s.symbol = latest.symbol AND s.date = latest.max_date
        ORDER BY s.daily_return DESC
        """
    ).fetchall()
    conn.close()

    data = [dict(r) for r in rows]
    return {
        "top_gainers": data[:top_n],
        "top_losers": data[-top_n:][::-1],
    }


@app.get("/volatility", tags=["Insights"], summary="Volatility ranking of all stocks")
def volatility_ranking():
    """Ranks all stocks by their volatility score (std dev of daily returns over last 30 days)."""
    conn = get_conn()
    symbols = [r[0] for r in conn.execute("SELECT DISTINCT symbol FROM stock_data").fetchall()]

    result = []
    for sym in symbols:
        rows = conn.execute(
            "SELECT daily_return, company_name FROM stock_data WHERE symbol=? ORDER BY date DESC LIMIT 30",
            (sym,),
        ).fetchall()
        if rows:
            returns = [r["daily_return"] for r in rows]
            avg = sum(returns) / len(returns)
            variance = sum((x - avg) ** 2 for x in returns) / len(returns)
            vol = round(math.sqrt(variance), 4)
            result.append({
                "symbol": sym,
                "company_name": rows[0]["company_name"],
                "volatility_score": vol,
                "label": "Low 🟢" if vol < 1.0 else "Medium 🟡" if vol < 2.0 else "High 🔴",
            })

    conn.close()
    return sorted(result, key=lambda x: x["volatility_score"], reverse=True)


@app.get("/correlation-matrix", tags=["Insights"], summary="Stock correlation matrix")
def correlation_matrix(days: int = Query(60, ge=30, le=252)):
    """
    Returns a full NxN correlation matrix between all available stocks.
    Useful for portfolio diversification analysis.
    """
    conn = get_conn()
    symbols = [r[0] for r in conn.execute("SELECT DISTINCT symbol FROM stock_data").fetchall()]

    prices = {}
    for sym in symbols:
        rows = conn.execute(
            "SELECT date, close FROM stock_data WHERE symbol=? ORDER BY date DESC LIMIT ?",
            (sym, days),
        ).fetchall()
        prices[sym] = {r["date"]: r["close"] for r in rows}

    conn.close()

    # Common dates across all
    all_dates = set.intersection(*[set(v.keys()) for v in prices.values()])
    all_dates = sorted(all_dates)

    series = {sym: [prices[sym][d] for d in all_dates] for sym in symbols}

    matrix = {}
    for s1 in symbols:
        matrix[s1] = {}
        for s2 in symbols:
            c1, c2 = series[s1], series[s2]
            n = len(c1)
            if n < 2:
                matrix[s1][s2] = 0
                continue
            m1, m2 = sum(c1) / n, sum(c2) / n
            num = sum((c1[i] - m1) * (c2[i] - m2) for i in range(n))
            d1 = math.sqrt(sum((c1[i] - m1) ** 2 for i in range(n)))
            d2 = math.sqrt(sum((c2[i] - m2) ** 2 for i in range(n)))
            matrix[s1][s2] = round(num / (d1 * d2), 3) if d1 and d2 else 1.0

    return {"symbols": symbols, "matrix": matrix, "days_used": len(all_dates)}


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
