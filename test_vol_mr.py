"""
Volatility-Screened Mean Reversion
Universe: full S&P 500, re-ranked daily by trailing 20-day realized
volatility (rolling stdev of daily returns) -- only the top VOL_TOP_N most
volatile names are eligible for new entries that day. Same BASIC_MR
SMA(20) dip-buy rule as test_basic_mr.py, plus a per-symbol cooldown: after
an exit, a symbol can't be re-entered for COOLDOWN_BARS bars, to stop the
strategy from immediately re-buying a name that just stopped out or
whipsawed back below the SMA.
"""
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import AlphaEngine
from AlphaEngine import StrategyType
import data_loader
from main import calculate_sharpe_ratio

INITIAL_CASH     = 10000.0
VOL_WINDOW       = 20     # trading days of returns used for realized vol
VOL_TOP_N        = 15     # most-volatile names eligible for entry each day
STOP_LOSS_PCT    = 0.07
TIME_STOP_BARS   = 20     # was 10 -- widened to cut down forced-exit churn
COOLDOWN_BARS    = 5
ENTRY_THRESHOLD  = 0.05   # was 0.03 (BasicMeanReversion default) -- wider dip required to enter

tickers = data_loader.get_sp500_tickers()

data       = data_loader.get_data_volatility(tickers, start="2024-01-01", end="2026-01-01",
                                              top_n=VOL_TOP_N, vol_window=VOL_WINDOW)
open_data = data["open"]
high_data = data["high"]
low_data  = data["low"]
close_data = data["close"]
daily_universe = data["daily_universe"]

# Sanity check: show one sample day's volatility-ranked universe.
sample_date = close_data.index[VOL_WINDOW + 5]
print(f"Sample volatile universe on {sample_date.date()}: {daily_universe.get(sample_date, [])}")

engine = AlphaEngine.AlphaEngine(INITIAL_CASH, StrategyType.BASIC_MR,
                                  STOP_LOSS_PCT, TIME_STOP_BARS, COOLDOWN_BARS, ENTRY_THRESHOLD)
equity_curve = []

for date in close_data.index:
    eligible_symbols = set(daily_universe.get(date, []))

    for symbol in close_data.columns:
        o = open_data.loc[date, symbol]
        h = high_data.loc[date, symbol]
        l = low_data.loc[date, symbol]
        c = close_data.loc[date, symbol]
        if np.isnan(c) or np.isnan(h) or np.isnan(o):
            continue
        engine.on_bar(symbol, float(o), float(h), float(l), float(c), symbol in eligible_symbols)

    equity_curve.append(engine.compute_equity())

engine.liquidate_all()

equity_array = np.array(equity_curve)
sharpe = calculate_sharpe_ratio(equity_array)

# Buy & hold #1: equal-weight basket of the same ~500 tickers used for the
# volatility screen -- NOT the real (cap-weighted) S&P 500 index, just the
# same universe held passively. A stock like AAPL gets the same dollar
# weight here as the smallest name in the list, so this tracks the "average
# stock" in the universe rather than what most people mean by "the S&P 500."
# Restricted to tickers with a valid close on day 1: get_sp500_tickers()
# returns TODAY's roster, so any name added to the index after 2024-01-01
# (e.g. SNDK, spun off from WDC in 2025) has NaN there -- including it in
# the denominator while its price column silently drops out of the sum
# understates the benchmark, since its slice of INITIAL_CASH never gets
# invested.
valid_cols       = close_data.columns[close_data.iloc[0].notna()]
shares_per_stock = (INITIAL_CASH / len(valid_cols)) / close_data[valid_cols].iloc[0]
bh_basket_curve  = (close_data[valid_cols] * shares_per_stock).sum(axis=1)
ending_value_bh  = bh_basket_curve.iloc[-1]

# Buy & hold #2: actual SPY (cap-weighted S&P 500 ETF) -- what "buy the
# S&P 500" normally means, included so the equal-weight basket isn't the
# only benchmark on the chart.
spy_close = yf.download("SPY", start="2024-01-01", end="2026-01-01")["Close"]
if isinstance(spy_close, pd.DataFrame):
    spy_close = spy_close["SPY"]
spy_shares      = INITIAL_CASH / spy_close.iloc[0]
spy_curve       = spy_close * spy_shares
ending_value_spy = spy_curve.iloc[-1]

def max_drawdown(series):
    running_max = series.cummax()
    drawdown    = (series - running_max) / running_max
    trough_date = drawdown.idxmin()
    peak_date   = series[:trough_date].idxmax()
    return drawdown.min(), peak_date, series[peak_date], trough_date, series[trough_date]

strategy_series = pd.Series(equity_curve, index=close_data.index)
strat_dd, strat_peak_date, strat_peak_val, strat_trough_date, strat_trough_val = max_drawdown(strategy_series)
spy_dd,   spy_peak_date,   spy_peak_val,   spy_trough_date,   spy_trough_val   = max_drawdown(spy_curve)

print(f"\nSharpe Ratio: {sharpe:.2f}")
print("==========================================")
print(f"YOUR STRATEGY VALUATION: ${engine.compute_equity():.2f}")
print(f"BUY & HOLD (equal-weight basket of same universe): ${ending_value_bh:.2f}")
print(f"BUY & HOLD (actual SPY / cap-weighted S&P 500):    ${float(ending_value_spy):.2f}")
print("------------------------------------------")
print(f"MAX DRAWDOWN (strategy): {strat_dd*100:.1f}%  "
      f"peak ${strat_peak_val:,.0f} on {strat_peak_date.date()}  ->  "
      f"trough ${strat_trough_val:,.0f} on {strat_trough_date.date()}")
print(f"MAX DRAWDOWN (SPY, same period): {spy_dd*100:.1f}%  "
      f"peak ${float(spy_peak_val):,.0f} on {spy_peak_date.date()}  ->  "
      f"trough ${float(spy_trough_val):,.0f} on {spy_trough_date.date()}")
print("==========================================")

plt.figure(figsize=(12, 6))
plt.plot(close_data.index, equity_curve, label=f"Strategy (Vol-Screened MR)  ${engine.compute_equity():,.0f}",
         color="lime", linewidth=1.5)
plt.plot(bh_basket_curve.index, bh_basket_curve.values,
         label=f"B&H equal-weight basket (same universe)  ${ending_value_bh:,.0f}",
         color="darkorange", linewidth=1.3, alpha=0.85)
plt.plot(spy_curve.index, spy_curve.values,
         label=f"B&H SPY (cap-weighted S&P 500)  ${float(ending_value_spy):,.0f}",
         color="royalblue", linewidth=1.3, alpha=0.85)
plt.axhline(INITIAL_CASH, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
plt.title("Volatility-Screened Mean Reversion vs. Buy & Hold (2024-2026)")
plt.ylabel("Portfolio Value ($)")
plt.legend()
plt.grid(True, alpha=0.2)
plt.tight_layout()
plt.savefig("vol_mr_equity_curve.png", dpi=130)
plt.show()
