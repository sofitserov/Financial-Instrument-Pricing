import matplotlib.pyplot as plt
import numpy as np

def calculate_sharpe_ratio(equity_history, risk_free_rate=0.0):
    daily_returns = np.diff(equity_history) / equity_history[:-1]
    
    avg_return = np.mean(daily_returns)
    std_return = np.std(daily_returns)
    
    if std_return == 0:
        return 0.0
    
    sharpe = (avg_return - risk_free_rate) / std_return * np.sqrt(252)
    return sharpe



def run_strategy_and_plot(engine, prices, params):
    engine.run(prices, params)
    equity_curve = np.array(engine.get_history())
    sharpe = calculate_sharpe_ratio(equity_curve)

    benchmark_prices = np.array(prices)

    strategy_returns = equity_curve / equity_curve[0]
    benchmark_returns = benchmark_prices / benchmark_prices[0]

    buys = engine.get_buy_signals()
    sells = engine.get_sell_signals()

    #Plotting
    plt.figure(figsize=(12, 6))

    plt.plot(strategy_returns, label=f"Strategy ({((strategy_returns[-1]-1)*100):.2f}%)", color="lime", linewidth=1.5, alpha=0.8)
    plt.plot(benchmark_returns, label=f"Buy & Hold ({((benchmark_returns[-1]-1)*100):.2f}%)", color="blue", alpha=0.5)
    plt.scatter(buys, benchmark_returns[buys], marker='^', color='green', s=50, label='Buy Signal', zorder=5)
    plt.scatter(sells, benchmark_returns[sells], marker='v', color='red', s=50, label='Sell Signal', zorder=5)

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
    print(f"Sharpe Ratio: {sharpe:.2f}")

