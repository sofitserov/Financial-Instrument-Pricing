**Setup**
Ensure you have a C++ compiler (Clang/GCC), CMake, and the required Python libraries installed:
```pip install yfinance pandas matplotlib```

We use CMake to manage the build process. This creates the AlphaEngine shared object file:
Create and enter build directory:
```mkdir build && cd build```

Generate build files and compile:
```cmake ..```
```make```

Move the compiled library back to the root directory:
```cp AlphaEngine.cpython-*.so ..```
```cd ..```

Run:
```python3 main.py```

**Phase 1:**
- Established a code architecture with CMake to combine python and c++ through pybind
- AlphaEngine is a hybrid quantitative backtesting framework that combines the research flexibility of Python with the execution power of C++.
- By using pybind11, the project offloads heavy mathematical computations and portfolio state management (tracking cash/positions) to a C++ core.

- Wrote a very basic algorithm to track a 20-day and 50-day moving average signal for Pepsi stock from 1/1/2024 - 1/1/2026

Performance Analysis: Test against baseline
The engine currently benchmarks active strategies against a passive Buy & Hold baseline.

| Metric | Value |
| :--- | :--- |
| **Strategy Return (20/50 SMA)** | -29.69% |
| **Benchmark Return (PEP)** | -10.81% |
| **Alpha** | -18.88% |

**Observation:** The negative alpha indicates the 20/50 SMA crossover is too lagging for current PEP volatility. This provides a baseline for future optimization using faster indicators or mean-reversion logic.

**Stateful vs. Stateless Backtesting**
- Most backtesters calculate a list of signals in Python without accounting for whether they actually have the money to buy the stock.
- By keeping cash and position as private members in C++ , the engine "remembers" the past. If all cash is spent on Monday, the C++ engine will automatically prevent a "Buy" on Tuesday, even if the signal is positive.
