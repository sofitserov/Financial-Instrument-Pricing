## Setup

### Ensure you have a C++ compiler (Clang/GCC) and CMake

1. Clone the Github repository
```bash
git clone https://github.com/sofitserov/Financial-Instrument-Pricing
```
2. Install the necessary python libraries
```bash
pip install yfinance pandas matplotlib numpy
```

### CMake is used for the build process. 3 & 4 create the AlphaEngine shared object file:
- Keep in mind that steps 4 and 5 must be run every time changes are made to strategy.hpp to update the so file

3. Create and enter build directory:
```bash
mkdir build
cd build
```

4. Generate build files and compile:
```bash
cmake ..
make
```

5. Move the compiled library back to the root directory:
```bash
cp AlphaEngine.cpython-*.so ..
cd ..
```

6. Run:
```bash
python3 test_mr.py
```

## 6/10/2026: 
- Universe Filter: Intersection of the top 15 strongest relative momentum stocks simultaneously ranked across 63-day, 126-day, and 252-day Rate of Change (ROC) windows.
- Portfolio Constraint: Maximum of 5 concurrent active positions across the entire portfolio.
- Position Sizing: Dynamic allocation using 10% of remaining liquid cash per trade trigger.
- Entry Trigger (Daily Close): Price breaks sharply below short-term trends relative to intermediate trends.
- Exit Triggers (Whichever occurs first):
  1. Profit Target
  2. Risk Stop: 3% Hard Stop Loss** relative to the execution entry price
  3. Time-Based Stop: Unconditional liquidation after holding an asset for 5 consecutive bars.

- Debugging:
    - The engine respects the global capacity cap. When the portfolio reaches 5 concurrent asset blocks, further entries are strictly blocked

    ENTRY BUY AMZN | Qty: 4 @ 196.01
    ENTRY BUY GOOGL | Qty: 5 @ 156.404
    ENTRY BUY META | Qty: 1 @ 582.114
    ENTRY BUY AAPL | Qty: 3 @ 202.122  <-- 4th Position
    ENTRY BUY MSFT | Qty: 2 @ 369.475  <-- 5th Position (Engine holds here)

    - The 5-bar tracking arrays successfully increment and enforce chronological timeouts.

    ENTRY BUY AAPL | Qty: 4 @ 236.053
    ... (5 Bars Elapsed)
    EXIT AAPL @ 234.093 | Reason: Time Stop

    - Stop Loss Calculations
        - Case (META):
        - Entry Price: `700.958`
        - Expected Risk Boundary: $700.958 \times (1 - 0.03) = \mathbf{679.92}$
        - Logged Execution Close: `665.46`

- Backtesting:
    - Initial Capital: $10,000.00
    - Ending Portfolio Value: $10,678.24
    - Net Return: +6.78%
    - Sharpe Ratio: 0.3 against 5% risk free rate

- Analysis:
    - While our initial backtest was profitable and beat a 5% savings rate hurdle, a Sharpe ratio of 0.30 means the strategy is leaving a lot of money on the table. By analyzing our trade logs, we found two major issues in how the code manages money, and we are rewriting the C++ engine to fix them:

1. Fixing the "Cash Hoarding" Problem
- Right now, the code sizes new trades using 10% of *remaining* cash. If you start with $10,000, your first trade uses $1,000. The next trade uses 10% of what's left ($900), the next uses $810, and so on. By the time you buy your 5th stock, you are barely putting any money into it. This means over 60% of your total account sits completely idle in cash doing nothing. In a booming stock market, holding that much cash severely drags down your total returns.
- We are rewriting the buying function to look at the total value of the entire portfolio (Cash + Open Positions), not just raw leftover cash. Every single trade will now get a flat 20% chunk of the total account value. This ensures that when we hold 5 stocks, we are 100% fully invested in the market.

2. Selling Completely Instead of Hanging On
- The legacy code only sells 50% of our shares when a stock hits its target. This leaves the other half of our shares floating in the market without an active plan, exposing us to random losses.
- Will updated the exit rules to sell 100% of our shares the exact moment a profit target, stop loss, or 5-day time limit is reached.

3. Giving Volatile Stocks More Room
- Right now, we use a strict 3% stop loss across the board. Tech stocks like Nvidia (NVDA) and Meta (META) jump up and down aggressively. A rigid 3% stop loss gets triggered by normal daily market noise, kicking us out of a great trade way too early.
- We are adding an Average True Range (ATR) indicator. This mathematically measures how volatile a stock is. The engine will automatically give a wild stock like Nvidia a wider stop loss, while keeping a tighter, safer stop loss on more stable stocks.

- Cash Hoard fix:
    - Even Cash Splitting: divides 100% of our available liquid cash balance evenly by the remaining slots (max of 5).
    - The Result:
        - This change completely eliminated our idle cash problem. When 5 qualified assets trigger signals, our money is 100% working in the market. This optimization alone successfully pushed our Sharpe Ratio from **0.30 to 0.84**


## 5/26/2026: File separation and bug fixes
- Bug prevented strategy from buying or selling multiple positions in a row
- main.py now contains 2 functions for calculating the Sharpe ratio as well as running the strategy and plotting results
- Added very simple position sizing where we buy 10% worth of our cash and sell 10% of our total position
- Next steps
    - Implement transaction costs and slippage
    - we also sometimes fall into the trap of having a negative position which requires investigation 

![Mean Reversion Strategy on S&P 500 from 01-01-2024 -- 01-01-2026](images/MR_SPY_1.png)
- The chart shows the mean reversion strategy on the S&P 500 from 01-01-2024 to 01-01-2026
- We can see that the strategy buys too aggressively during downturns, so it would be useful to consider more signals before buying
- Perhaps it would be useful to experiment with time-based trades as well as the MR strategy

## 5/24/2026: Overhaul for future expansion
- C++ now handles the moving average calculations 
- strategy.hpp
    - Created an AlphaEngine class which will contain all of the logic for strategies implemented in the future.
    - AlphaEngine objects have StrategyType member variable, which dictate which strategy function to run.
- main.py
    - choose the strategy when creating the AlphaEngine object
    - Compare to benchmark and break-even point
    - Moving average values are no longer hard-coded and are passed as parameters to the run function.

## 5/22/2026: Setup
- Established a code architecture with CMake to combine python and c++ through pybind
- AlphaEngine is a hybrid quantitative backtesting framework that combines the flexibility of Python with the execution power of C++.
- By using pybind11, the project offloads heavy computations and portfolio state management (tracking cash/positions) to C++.

- Wrote a very basic algorithm to track a 20-day and 50-day moving average signal for Pepsi stock from 1/1/2024 - 1/1/2026 to ensure all parts were working as intended

Performance Analysis: Test against baseline
The engine currently benchmarks active strategies against a passive Buy & Hold baseline.

| Metric | Value |
| :--- | :--- |
| **Strategy Return (20/50 SMA)** | -29.69% |
| **Benchmark Return (PEP)** | -10.81% |
| **Alpha** | -18.88% |

### Observation: 
- The negative alpha indicates the 20/50 SMA crossover is too slow for current volatility. 
- This provides a baseline for future optimization using faster indicators or mean-reversion logic. But we are not too worried about the actual strategy at the moment.

### Stateful vs. Stateless Backtesting
- By keeping cash and position as private members in C++ , the engine logs our cash balance. 
- If all cash is spent, the C++ engine will automatically prevent a future buy.








