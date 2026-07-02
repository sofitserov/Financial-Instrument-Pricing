"""
Basic Mean Reversion — walk-forward validation.
Each fold: grid search on all data up to year Y, test on year Y+1.
Produces a stitched out-of-sample equity curve across all test years.
"""
import os
import ctypes
import contextlib
import numpy as np
import matplotlib.pyplot as plt
import AlphaEngine
from AlphaEngine import StrategyType
import data_loader
from main import calculate_sharpe_ratio

_libc = ctypes.CDLL(None)

@contextlib.contextmanager
def suppress_cpp_stdout():
    devnull = os.open(os.devnull, os.O_WRONLY)
    saved   = os.dup(1)
    os.dup2(devnull, 1)
    try:
        yield
    finally:
        _libc.fflush(None)   # flush all C/C++ buffers into devnull before restoring
        os.dup2(saved, 1)
        os.close(saved)
        os.close(devnull)

INITIAL_CASH = 10000.0

tickers = [
    "AAPL", "MSFT", "NVDA", "META", "AMZN", "GOOGL", "AVGO", "ORCL", "CRM", "AMD",
    "UNH",  "JNJ",  "LLY",  "PFE",  "ABBV",
    "JPM",  "BAC",  "V",    "MA",   "GS",
    "WMT",  "HD",   "PG",   "KO",   "PEP",  "MCD",
    "XOM",  "CVX",  "CAT",  "BA",
]

data       = data_loader.get_data2(tickers, start="2015-01-01", end="2026-01-01")
open_data  = data["open"]
high_data  = data["high"]
low_data   = data["low"]
close_data = data["close"]

def run_backtest(dates, stop_loss_pct, time_stop_bars, cash=INITIAL_CASH):
    engine = AlphaEngine.AlphaEngine(cash, StrategyType.BASIC_MR,
                                     stop_loss_pct, time_stop_bars)
    curve = []
    for date in dates:
        for symbol in close_data.columns:
            o = open_data.loc[date, symbol]
            h = high_data.loc[date, symbol]
            l = low_data.loc[date, symbol]
            c = close_data.loc[date, symbol]
            if np.isnan(c) or np.isnan(h) or np.isnan(o):
                continue
            engine.on_bar(symbol, float(o), float(h), float(l), float(c))
        curve.append(engine.compute_equity())
    engine.liquidate_all()
    return np.array(curve)

stop_loss_grid = [0.05, 0.08, 0.12, 0.17, 0.22]
time_stop_grid = [10, 20, 30]

# Walk-forward: train on 2015–(Y-1), test on year Y
# Minimum 3 years of train data → first test year is 2018
test_years = list(range(2018, 2026))

fold_results = []   # (test_year, best_sl, best_ts, train_sharpe, test_curve, test_dates)

print(f"{'Fold':<6} {'Train window':<26} {'Test year':<11} "
      f"{'Best SL':>8} {'Best TS':>8} {'Train Sh':>9} {'Test Sh':>8} {'Test Ret':>9}")
print("-" * 90)

for test_year in test_years:
    train_dates = close_data.index[close_data.index.year <  test_year]
    test_dates  = close_data.index[close_data.index.year == test_year]
    if len(train_dates) == 0 or len(test_dates) == 0:
        continue

    # Grid search on train
    best_sharpe, best_sl, best_ts = -np.inf, None, None
    for sl in stop_loss_grid:
        for ts in time_stop_grid:
            with suppress_cpp_stdout():
                curve = run_backtest(train_dates, sl, ts)
            s = calculate_sharpe_ratio(curve)
            if s > best_sharpe:
                best_sharpe, best_sl, best_ts = s, sl, ts

    # Evaluate on test year
    with suppress_cpp_stdout():
        test_curve = run_backtest(test_dates, best_sl, best_ts)

    test_sharpe = calculate_sharpe_ratio(test_curve)
    test_ret    = (test_curve[-1] / INITIAL_CASH - 1) * 100

    fold_results.append((test_year, best_sl, best_ts, best_sharpe, test_curve, test_dates))

    print(f"{test_year:<6} {str(train_dates[0].date())+' → '+str(train_dates[-1].date()):<26} "
          f"{str(test_dates[0].date()):<11} "
          f"{best_sl:>7.0%}  {best_ts:>6}d  {best_sharpe:>+8.2f}  "
          f"{test_sharpe:>+7.2f}  {test_ret:>+8.1f}%")

# Stitch test curves end-to-end, compounding equity
stitched_curve  = []
stitched_dates  = []
stitched_bh     = []
running_cash    = INITIAL_CASH

shares = (INITIAL_CASH / len(close_data.columns)) / close_data.iloc[0]
bh_full = (close_data * shares).sum(axis=1)

for (test_year, best_sl, best_ts, _, raw_curve, test_dates) in fold_results:
    # Re-run test with actual starting cash (compounded from prior folds)
    with suppress_cpp_stdout():
        curve = run_backtest(test_dates, best_sl, best_ts, cash=running_cash)

    # Scale buy-and-hold to match starting cash for this fold
    bh_period = bh_full[test_dates]
    bh_scaled = bh_period.values * (running_cash / bh_period.iloc[0])

    stitched_curve.extend(curve.tolist())
    stitched_dates.extend(test_dates.tolist())
    stitched_bh.extend(bh_scaled.tolist())
    running_cash = curve[-1]

stitched_curve = np.array(stitched_curve)
stitched_bh    = np.array(stitched_bh)

overall_sharpe = calculate_sharpe_ratio(stitched_curve)
overall_ret    = (stitched_curve[-1] / INITIAL_CASH - 1) * 100
bh_ret         = (stitched_bh[-1]   / INITIAL_CASH - 1) * 100

print("-" * 90)
print(f"\nOut-of-sample (stitched):  Strategy {overall_ret:+.1f}%  Sharpe {overall_sharpe:.2f}  "
      f"|  Buy&Hold {bh_ret:+.1f}%")

# --- Plots ---
test_sharpes = [calculate_sharpe_ratio(r[4]) for r in fold_results]
years        = [r[0] for r in fold_results]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 9),
                                gridspec_kw={"height_ratios": [3, 1]})
fig.suptitle("Basic Mean Reversion — Walk-Forward Validation (2018–2025)", fontsize=13)

# Stitched equity curve
ax1.plot(stitched_dates, stitched_curve, color="royalblue", linewidth=1.5,
         label=f"Strategy (stitched OOS)  {overall_ret:+.1f}%  Sharpe {overall_sharpe:.2f}")
ax1.plot(stitched_dates, stitched_bh,    color="darkorange", linewidth=1.5, alpha=0.8,
         label=f"Buy & Hold  {bh_ret:+.1f}%")
ax1.axhline(INITIAL_CASH, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)

# Shade alternating test years
for i, (test_year, *_) in enumerate(fold_results):
    yr_dates = [d for d in stitched_dates if d.year == test_year]
    if yr_dates and i % 2 == 0:
        ax1.axvspan(yr_dates[0], yr_dates[-1], alpha=0.06, color="gray")

ax1.set_ylabel("Portfolio Value ($)")
ax1.legend()
ax1.grid(True, alpha=0.2)

# Per-year test Sharpe bar chart
colors = ["steelblue" if s >= 0 else "tomato" for s in test_sharpes]
ax2.bar(years, test_sharpes, color=colors, width=0.6)
ax2.axhline(0, color="gray", linewidth=0.8)
ax2.set_ylabel("Test Sharpe")
ax2.set_xlabel("Test Year")
ax2.set_xticks(years)
ax2.grid(True, alpha=0.2, axis="y")

fig.tight_layout()
plt.show()
