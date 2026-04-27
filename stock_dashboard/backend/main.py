"""
Stock Data Intelligence Dashboard - Backend API
Built with FastAPI + SQLite + yfinance
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os

from database import init_db, SessionLocal
from data_fetcher import fetch_and_store_all
from crud import (
    get_companies,
    get_stock_data,
    get_summary,
    compare_stocks,
    get_top_gainers_losers,
    get_correlation,
)

app = FastAPI(
    title="Stock Data Intelligence Dashboard",
    description="A mini financial data platform for NSE stock analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_PATH):
    app.mount("/static", StaticFiles(directory=FRONTEND_PATH), name="static")


@app.on_event("startup")
async def startup_event():
    init_db()
    print("Fetching stock data... (this may take a moment on first run)")
    fetch_and_store_all()
    print("✅ Stock data ready!")


@app.get("/", include_in_schema=False)
async def root():
    index_path = os.path.join(FRONTEND_PATH, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Stock Dashboard API is running. Visit /docs for Swagger UI."}


@app.get("/companies", tags=["Stock Data"], summary="List all available companies")
def list_companies():
    """Returns list of all available companies with metadata."""
    db = SessionLocal()
    try:
        return get_companies(db)
    finally:
        db.close()


@app.get("/data/{symbol}", tags=["Stock Data"], summary="Get historical stock data")
def stock_data(symbol: str, days: int = Query(30, ge=1, le=365, description="Number of days")):
    """Returns last N days of OHLCV data + calculated metrics for a given symbol."""
    db = SessionLocal()
    try:
        data = get_stock_data(db, symbol.upper(), days)
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")
        return {"symbol": symbol.upper(), "days": days, "data": data}
    finally:
        db.close()


@app.get("/summary/{symbol}", tags=["Stock Data"], summary="52-week summary")
def stock_summary(symbol: str):
    """Returns 52-week high, low, avg close, volatility score, and momentum."""
    db = SessionLocal()
    try:
        summary = get_summary(db, symbol.upper())
        if not summary:
            raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")
        return summary
    finally:
        db.close()


@app.get("/compare", tags=["Stock Data"], summary="Compare two stocks")
def compare(
    symbol1: str = Query(..., description="First stock symbol e.g. RELIANCE.NS"),
    symbol2: str = Query(..., description="Second stock symbol e.g. TCS.NS"),
):
    """Compare two stocks' normalized performance over last 90 days."""
    db = SessionLocal()
    try:
        result = compare_stocks(db, symbol1.upper(), symbol2.upper())
        if not result:
            raise HTTPException(status_code=404, detail="Data not found for one or both symbols")
        return result
    finally:
        db.close()


@app.get("/gainers-losers", tags=["Insights"], summary="Top gainers and losers")
def gainers_losers(top_n: int = Query(5, ge=1, le=20)):
    """Returns top N gainers and losers based on latest daily return."""
    db = SessionLocal()
    try:
        return get_top_gainers_losers(db, top_n)
    finally:
        db.close()


@app.get("/correlation", tags=["Insights"], summary="Correlation between two stocks")
def correlation(
    symbol1: str = Query(...),
    symbol2: str = Query(...),
):
    """Returns Pearson correlation coefficient between two stocks' daily returns."""
    db = SessionLocal()
    try:
        result = get_correlation(db, symbol1.upper(), symbol2.upper())
        if result is None:
            raise HTTPException(status_code=404, detail="Insufficient data for correlation")
        return result
    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
