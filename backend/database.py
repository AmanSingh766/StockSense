"""
Database configuration and models using SQLAlchemy + SQLite
"""

from sqlalchemy import create_engine, Column, String, Float, Date, Integer, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./stock_data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class StockData(Base):
    __tablename__ = "stock_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    company_name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    daily_return = Column(Float)         # (close - open) / open
    ma_7 = Column(Float)                 # 7-day moving average
    ma_20 = Column(Float)                # 20-day moving average
    volatility = Column(Float)           # Rolling 7-day std of daily returns
    week52_high = Column(Float)
    week52_low = Column(Float)

    __table_args__ = (UniqueConstraint("symbol", "date", name="uq_symbol_date"),)


def init_db():
    Base.metadata.create_all(bind=engine)
