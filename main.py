import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def calculate_sharpe_ratio(equity_history, risk_free_rate=0.05):
    # 1. Calculate daily returns
    equity_series = pd.Series(equity_history)
    daily_returns = equity_series.pct_change().dropna()
    
    if daily_returns.std() == 0:
        return 0.0
        
    # 2. Deconstruct the annualized risk-free rate down to a DAILY risk-free rate
    # 252 trading days in a typical market year
    daily_rf = risk_free_rate / 252 
    
    # 3. Calculate Daily Sharpe
    expected_daily_excess_return = daily_returns.mean() - daily_rf
    daily_sharpe = expected_daily_excess_return / daily_returns.std()
    
    # 4. Annualize the Sharpe Ratio correctly using the square-root of time rule
    annualized_sharpe = daily_sharpe * np.sqrt(252)
    
    return annualized_sharpe



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

