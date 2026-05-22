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