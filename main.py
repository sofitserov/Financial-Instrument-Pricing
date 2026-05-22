import AlphaEngine  # This imports your .so file
import yfinance as yf
import matplotlib.pyplot as plt

# 1. Download real market data
data = yf.download("PEP", start="2024-01-01", end="2026-01-01")['Close']
prices = data.values.flatten().tolist()

# 2. Initialize your C++ Strategy
strat = AlphaEngine.MAStrategy()

# 3. Generate signals for the timeline
signals = []
for i in range(len(prices)):
    # Feed the growing list of prices to C++
    sig = strat.generate_signal(prices[:i+1], 20, 50)
    signals.append(sig)

# 4. Comprehensive Visualization
plt.figure(figsize=(12, 6))

# Plot the raw price data
plt.plot(prices, label="PEP Price", color='blue', alpha=0.3)

# Calculate SMAs using Pandas for visual comparison
import pandas as pd
price_series = pd.Series(prices)
sma20 = price_series.rolling(window=20).mean()
sma50 = price_series.rolling(window=50).mean()

# Plot the Moving Averages
plt.plot(sma20, label="20d SMA (Fast)", color='orange', linewidth=1.5)
plt.plot(sma50, label="50d SMA (Slow)", color='green', linewidth=1.5)

plt.title("C++ Powered Strategy: PEP Price + Moving Averages")
plt.xlabel("Days")
plt.ylabel("Price (USD)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show() # This will now show everything in one window

print(f"Final Portfolio Value: ${strat.get_balance() + (strat.get_position() * prices[-1])}")

# While inside the 'build' folder:
#cp AlphaEngine.cpython-313-darwin.so ..
#Every time you touch a .hpp or .cpp file, you must follow this 3-step ritual:
#1. Modify: Change the C++ logic or add a new binding in wrapper.cpp.
#2. Rebuild: Run `cmake .. && make` inside the 'build' folder to recompile the .so file.
#3. Refresh: Restart this Python script to see the changes in action.

# --- Performance Benchmarking ---
initial_capital = 10000.0

# 1. Strategy Performance (C++ Core)
# Total = Current Cash + (Shares Held * Current Price)
strategy_final_total = strat.get_balance() + (strat.get_position() * prices[-1])
strategy_return_pct = ((strategy_final_total - initial_capital) / initial_capital) * 100

# 2. Buy & Hold Performance (The Benchmark)
# How many shares could we buy on day 1?
shares_to_buy = initial_capital // prices[0] 
remaining_cash = initial_capital % prices[0]
# Value today = (Shares * Current Price) + leftover cash
buy_hold_final_total = (shares_to_buy * prices[-1]) + remaining_cash
buy_hold_return_pct = ((buy_hold_final_total - initial_capital) / initial_capital) * 100

print("\n" + "="*30)
print(f"STRATEGY VS BENCHMARK")
print("="*30)
print(f"C++ Strategy Final:  ${strategy_final_total:.2f} ({strategy_return_pct:.2f}%)")
print(f"Buy & Hold Final:    ${buy_hold_final_total:.2f} ({buy_hold_return_pct:.2f}%)")
print(f"Alpha (Difference):  {strategy_return_pct - buy_hold_return_pct:.2f}%")
print("="*30)