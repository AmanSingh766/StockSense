# 🚀 StockSense — NSE Stock Intelligence Dashboard

A full-stack financial data platform built with **FastAPI + SQLite + yfinance + Chart.js**.

---

## 📌 Features

* 📊 Live & mock NSE stock data (15 blue-chip stocks)
* ⚡ FastAPI backend with 6 REST APIs
* 📈 Technical indicators:

  * Daily Return
  * MA-7, MA-20
  * Volatility Score
  * 30-Day Momentum
* 📉 Stock comparison (normalized performance)
* 🏆 Top gainers & losers
* 🔗 Correlation analysis (Pearson)
* 🌙 Modern dark-themed UI (Chart.js)

---

## 🏗️ Project Structure

```
StockSense_Dashboard/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── data_fetcher.py
│   ├── crud.py
│   └── mock_data.py
│
├── frontend/
│   └── index.html
│
├── requirements.txt
├── runtime.txt
├── README.md
```

---

## ⚙️ Setup & Run (Local)

### 1️⃣ Clone repo

```bash
git clone https://github.com/AmanSingh766/StockSense.git
cd StockSense_Dashboard
```

---

### 2️⃣ Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

---

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Run server

```bash
python -m uvicorn backend.main:app --reload
```

---

### 5️⃣ Open in browser

* 🌐 Dashboard → http://127.0.0.1:8000
* 📄 API Docs → http://127.0.0.1:8000/docs

---

## 📡 API Endpoints

| Endpoint            | Description               |
| ------------------- | ------------------------- |
| `/companies`        | List all stocks           |
| `/data/{symbol}`    | Historical data + metrics |
| `/summary/{symbol}` | 52-week insights          |
| `/compare`          | Compare 2 stocks          |
| `/gainers-losers`   | Top movers                |
| `/correlation`      | Stock correlation         |

---

## 📊 Metrics Explained

| Metric         | Description                 |
| -------------- | --------------------------- |
| Daily Return   | (Close - Open) / Open       |
| MA-7 / MA-20   | Moving averages             |
| Volatility     | Risk indicator              |
| Momentum (30D) | Trend strength              |
| Correlation    | Relationship between stocks |

---

## ⚠️ Notes

* If **yfinance fails**, app automatically uses **mock data**
* First run may take **30–60 seconds** (data fetching)
* SQLite DB is created automatically

---

## 🌐 Deployment (Render)

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 10000
```

---

## 👨‍💻 Tech Stack

* Backend: FastAPI, SQLAlchemy
* Database: SQLite
* Data: Pandas, yfinance
* Frontend: HTML, JS, Chart.js

---

## 💼 Author

**Aman Singh**
B.Tech CSE (Cloud + Security)

---

## ⭐ Final Note

This project demonstrates:

* Backend API development
* Data processing & analytics
* Full-stack integration
* Real-world deployment

---

✨ Ready for internship & production-level showcase
