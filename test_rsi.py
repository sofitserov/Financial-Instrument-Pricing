import AlphaEngine
from AlphaEngine import StrategyType
from main import calculate_sharpe_ratio
import data_loader
import numpy as np

tickers = [
    "AAPL", "MSFT", "NVDA", "META", "AMZN", "GOOGL", "AVGO", "ORCL", "CRM", "AMD",
    "UNH", "JNJ", "LLY", "PFE", "ABBV",
    "JPM", "BAC", "V", "MA", "GS",
    "WMT", "HD", "PG", "KO", "PEP", "MCD",
    "XOM", "CVX", "CAT", "BA",
]
data = data_loader.get_data2(tickers, start="2024-01-01", end="2026-01-01")

open_data  = data["open"]
high_data  = data["high"]
low_data   = data["low"]
close_data = data["close"]
daily_universe = data["daily_universe"]

def rsi(series, period=5):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, float('nan'))
    return (100 - 100 / (1 + rs)).fillna(100)

# RSI(5) for all stocks: used to sort candidates by most oversold (transaction weight)
stock_rsi = close_data.apply(lambda col: rsi(col))

engine = AlphaEngine.AlphaEngine(10000.0, StrategyType.RSI)
equity_curve = []

for date in close_data.index:
    eligible_symbols = set(daily_universe.get(date, []))

    # Transaction weight: sort stocks by RSI ascending so most oversold get first slot
    day_rsi = stock_rsi.loc[date] if date in stock_rsi.index else None
    if day_rsi is not None:
        sorted_symbols = day_rsi.sort_values().index.tolist()
    else:
        sorted_symbols = close_data.columns.tolist()

    for symbol in sorted_symbols:
        if symbol not in close_data.columns:
            continue
        o = open_data.loc[date, symbol]
        h = high_data.loc[date, symbol]
        l = low_data.loc[date, symbol]
        c = close_data.loc[date, symbol]
        if np.isnan(c) or np.isnan(h) or np.isnan(o):
            continue
        eligible = symbol in eligible_symbols
        engine.on_bar(symbol, float(o), float(h), float(l), float(c), eligible)

    equity_curve.append(engine.compute_equity())

engine.liquidate_all()

sharpe = calculate_sharpe_ratio(np.array(equity_curve))
initial_investment = 10000.0
shares_per_stock = (initial_investment / len(close_data.columns)) / close_data.iloc[0]
ending_value_bh = (close_data.iloc[-1] * shares_per_stock).sum()

print(f"\nSharpe Ratio: {sharpe:.2f}")
print(f"==========================================")
print(f"YOUR STRATEGY VALUATION: ${engine.compute_equity():.2f}")
print(f"BUY & HOLD BENCHMARK VALUATION: ${ending_value_bh:.2f}")
print(f"==========================================")
