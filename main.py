import AlphaEngine
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from AlphaEngine import StrategyType

# Market data
data = yf.download("PEP", start="2024-01-01", end="2026-01-01")['Close']
prices = data.values.flatten().tolist()


# Initialize C++ Strategy with Type
engine = AlphaEngine.AlphaEngine(10000.0, StrategyType.SMA)

# Define Parameters for the Strategy
# Replaces the hardcoded 20, 50 
sma_params = {
    "fast_w": 10.0,
    "slow_w": 30.0
}
# Run the strategy
engine.run(prices, sma_params)

# Get equity curve from strategy to later plot against benchmark
equity_curve = engine.get_history()

#Get raw data for benchmark (Buy & Hold)
equity_curve = np.array(engine.get_history())
benchmark_prices = np.array(prices)


# Visualization
strategy_returns = equity_curve / equity_curve[0]
benchmark_returns = benchmark_prices / benchmark_prices[0]

buys = engine.get_buy_signals()
sells = engine.get_sell_signals()

#Plotting
plt.figure(figsize=(12, 6))

plt.plot(strategy_returns, label=f"Strategy ({((strategy_returns[-1]-1)*100):.2f}%)", color="lime", linewidth=1.5, alpha=0.8)
plt.plot(benchmark_returns, label=f"Buy & Hold PEP ({((benchmark_returns[-1]-1)*100):.2f}%)", color="blue", alpha=0.5)
plt.scatter(buys, benchmark_returns[buys], marker='^', color='green', s=100, label='Buy Signal', zorder=5)
plt.scatter(sells, benchmark_returns[sells], marker='v', color='red', s=100, label='Sell Signal', zorder=5)

#Line at 1.0 - Break-even point
plt.axhline(y=1.0, color='black', linestyle='--', alpha=0.3)

plt.title("Relative Performance: Strategy vs. Benchmark")
plt.ylabel("Cumulative Return (Multiple of Initial Investment)")
plt.legend()
plt.grid(True, alpha=0.2)
plt.show()

# Extract Results
final_balance = engine.get_balance()
print(f"Strategy finished. Final Balance: ${final_balance:.2f}")

# Compare to benchmark
final_strategy_pct = (strategy_returns[-1] - 1) * 100
final_benchmark_pct = (benchmark_returns[-1] - 1) * 100

alpha = final_strategy_pct - final_benchmark_pct

print("\n" + "="*30)
print("PERFORMANCE SUMMARY")
print("="*30)
print(f"Strategy Return:  {final_strategy_pct:>8.2f}%")
print(f"Benchmark Return: {final_benchmark_pct:>8.2f}%")
print("-" * 30)
print(f"Alpha (Difference): {alpha:>7.2f}%")
print("="*30)


