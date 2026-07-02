"""
Basic Mean Reversion Strategy via C++ AlphaEngine (BASIC_MR)
Entry: close > 3% below SMA(20). Exit: close reverts to SMA(20).
Max 5 simultaneous positions, equal cash allocation.

Restored from an earlier session (6/28-29) after test_mr_py.py evolved
into the walk-forward validation script. This was the best single-run
result so far: Sharpe 1.34 in pure Python, 1.14 once ported to C++.
"""
import numpy as np
import AlphaEngine
from AlphaEngine import StrategyType
import data_loader
from main import calculate_sharpe_ratio

INITIAL_CASH = 10000.0

tickers = [
    "AAPL", "MSFT", "NVDA", "META", "AMZN", "GOOGL", "AVGO", "ORCL", "CRM", "AMD",
    "UNH",  "JNJ",  "LLY",  "PFE",  "ABBV",
    "JPM",  "BAC",  "V",    "MA",   "GS",
    "WMT",  "HD",   "PG",   "KO",   "PEP",  "MCD",
    "XOM",  "CVX",  "CAT",  "BA",
]

data       = data_loader.get_data2(tickers, start="2024-01-01", end="2026-01-01")
open_data  = data["open"]
high_data  = data["high"]
low_data   = data["low"]
close_data = data["close"]

engine       = AlphaEngine.AlphaEngine(INITIAL_CASH, StrategyType.BASIC_MR)
equity_curve = []

for date in close_data.index:
    for symbol in close_data.columns:
        o = open_data.loc[date, symbol]
        h = high_data.loc[date, symbol]
        l = low_data.loc[date, symbol]
        c = close_data.loc[date, symbol]
        if np.isnan(c) or np.isnan(h) or np.isnan(o):
            continue
        # No momentum-universe gating: eligible_for_entry defaults to True
        engine.on_bar(symbol, float(o), float(h), float(l), float(c))

    equity_curve.append(engine.compute_equity())

engine.liquidate_all()

equity_array = np.array(equity_curve)
sharpe       = calculate_sharpe_ratio(equity_array)

shares_per_stock = (INITIAL_CASH / len(close_data.columns)) / close_data.iloc[0]
ending_value_bh  = (close_data.iloc[-1] * shares_per_stock).sum()

print(f"\nSharpe Ratio: {sharpe:.2f}")
print("==========================================")
print(f"YOUR STRATEGY VALUATION: ${engine.compute_equity():.2f}")
print(f"BUY & HOLD BENCHMARK VALUATION: ${ending_value_bh:.2f}")
print("==========================================")
