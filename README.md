# StockSense — NSE Stock Intelligence Dashboard

A full-stack financial data platform built with FastAPI + SQLite + yfinance + Chart.js for the Jarnox Internship Assignment.

## Features
- 15 blue-chip NSE stocks fetched live via yfinance
- 6 REST API endpoints with Swagger docs
- Calculated metrics: Daily Return, MA-7, MA-20, Volatility Score, 30D Momentum
- Beautiful dark-themed single-page dashboard with Chart.js
- Stock comparison (normalized performance)
- Top Gainers/Losers
- Pearson correlation between any two stocks

## Project Structure
```
stock_dashboard/
├── backend/
│   ├── main.py          # FastAPI app + API routes
│   ├── database.py      # SQLAlchemy ORM models
│   ├── data_fetcher.py  # yfinance download + Pandas cleaning
│   └── crud.py          # DB query functions
├── frontend/
│   └── index.html       # Dashboard (Chart.js)
├── requirements.txt
└── README.md
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the server
```bash
cd backend
python main.py
```
On first run, ~1 year of NSE stock data is downloaded (~30-60 seconds).

### 3. Open in browser
- Dashboard: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /companies | GET | All companies with latest price |
| /data/{symbol} | GET | Historical OHLCV + metrics |
| /summary/{symbol} | GET | 52-week high/low, volatility, momentum |
| /compare?symbol1=X&symbol2=Y | GET | Normalized 90-day comparison |
| /gainers-losers | GET | Top gainers and losers |
| /correlation?symbol1=X&symbol2=Y | GET | Pearson correlation |

## Calculated Metrics

| Metric | Formula |
|--------|---------|
| Daily Return | (Close - Open) / Open |
| 7-Day MA | Rolling 7-day average of close |
| 20-Day MA | Rolling 20-day average of close |
| Volatility Score | Rolling 7-day std of daily returns |
| 52-Week High/Low | Rolling max/min over 252 days |
| Momentum (30D) | % change from 30 days ago |
| Correlation | Pearson r of daily returns (90 days) |

## Custom Insights Added
1. Volatility Score — Rolling std of daily returns (risk indicator)
2. 30D Momentum — Trend direction over the last month
3. Pearson Correlation API — How two stocks move together
4. Normalized Comparison Chart — Fair relative performance view
5. Top Gainers/Losers — Dynamic daily ranking

## Tech Stack
- Backend: Python 3.11, FastAPI, SQLAlchemy, SQLite
- Data: yfinance, Pandas, NumPy
- Frontend: HTML/CSS/JS, Chart.js 4
