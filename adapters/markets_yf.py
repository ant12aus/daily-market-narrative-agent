from __future__ import annotations
import yfinance as yf
from datetime import datetime

TICKERS = {
    "ES": "ES=F",
    "NQ": "NQ=F",
    "DJ": "YM=F",
    "VIX": "^VIX",
    "DXY": "DX-Y.NYB",
    "WTI": "CL=F",
    "GOLD": "GC=F",
    "UST10Y": "^TNX",  # *10, so 42.10 = 4.21%
}

def pct_change(ticker: str):
    data = yf.Ticker(ticker).history(period="2d")
    if len(data) < 2:
        return None
    prev, curr = data["Close"].iloc[-2], data["Close"].iloc[-1]
    if prev == 0:
        return None
    return (curr - prev) / prev * 100

def get_markets_snapshot():
    snap = {"timestamp": datetime.utcnow().isoformat() + "Z"}
    for k, v in TICKERS.items():
        try:
            snap[k] = pct_change(v)
        except Exception:
            snap[k] = None
    return snap
