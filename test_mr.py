import AlphaEngine
from AlphaEngine import StrategyType
from main import calculate_sharpe_ratio, run_strategy_and_plot
import data_loader
import numpy as np

tickers = [
    # Tech
    "AAPL", "MSFT", "NVDA", "META", "AMZN", "GOOGL", "AVGO", "ORCL", "CRM", "AMD",
    # Healthcare
    "UNH", "JNJ", "LLY", "PFE", "ABBV",
    # Financials
    "JPM", "BAC", "V", "MA", "GS",
    # Consumer
    "WMT", "HD", "PG", "KO", "PEP", "MCD",
    # Industrials / Energy
    "XOM", "CVX", "CAT", "BA",
]
data = data_loader.get_data2(tickers, start="2024-01-01", end="2026-01-01")

# Unpack the richer OHLC data dictionary
open_data  = data["open"]
high_data  = data["high"]
low_data   = data["low"]
close_data = data["close"]
daily_universe = data["daily_universe"]

equity_curve = []

# Instantiate backtest environment state
engine = AlphaEngine.AlphaEngine(10000.0, StrategyType.MEAN_REVERSION)

# Step forward day-by-day through the simulation
for date in close_data.index:
    eligible_symbols = set(daily_universe.get(date, []))

    for symbol in close_data.columns:
        # Extract individual asset bar records for the day
        o_price = open_data.loc[date, symbol]
        h_price = high_data.loc[date, symbol]
        l_price = low_data.loc[date, symbol]
        c_price = close_data.loc[date, symbol]

        # Ensure no NaN attributes disrupt calculation boundaries
        if np.isnan(c_price) or np.isnan(h_price) or np.isnan(o_price):
            continue

        # Stream full OHLC values into the polymorphic C++ strategy layer.
        # The momentum filter only gates new entries; held positions are
        # always processed so exits/stops are never skipped.
        engine.on_bar(symbol, float(o_price), float(h_price), float(l_price), float(c_price), symbol in eligible_symbols)

    # Accumulate dynamic system valuation entries
    equity = engine.compute_equity()
    equity_curve.append(equity)

# Flush remaining asset inventories down to cash
engine.liquidate_all()

equity_array = np.array(equity_curve)
sharpe_score = calculate_sharpe_ratio(equity_array)

"""print("\n" + "="*40)
print(f"BACKTEST PROCESS COMPLETED SUCCESSFULLY")
print(f"Ending Liquid Portfolio Cash Balance: ${engine.get_balance():.2f}")
print(f"Ending Consolidated Portfolio Valuation: ${engine.compute_equity():.2f}")
"""
print(f"\nSharpe Ratio: {sharpe_score:.2f}")


initial_investment = 10000.0
shares_per_stock = (initial_investment / len(close_data.columns)) / close_data.iloc[0]
ending_value_bh = (close_data.iloc[-1] * shares_per_stock).sum()

print(f"==========================================")
print(f"YOUR STRATEGY VALUATION: ${engine.compute_equity():.2f}")
print(f"BUY & HOLD BENCHMARK VALUATION: ${ending_value_bh:.2f}")
print(f"==========================================")



