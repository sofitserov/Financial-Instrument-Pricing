## AlphaEngine

A C++/Python backtesting framework (pybind11) used to test technical trading strategies. The result of most of that testing: the strategies don't hold up. That's the actual point of this repo — it's a log of catching overfitting, look-ahead bias, and accounting bugs that make a backtest look better than it is, not a claim of having found alpha. Every result below is reported after those checks, including the ones that survive it looking mediocre.

### Setup

1. `pip install yfinance pandas matplotlib numpy statsmodels`
2. Build the C++ extensions:
   ```bash
   mkdir -p build && cd build
   cmake .. && make
   cp AlphaEngine.cpython-*.so AlphaEnginePairs.cpython-*.so ..
   cd ..
   ```
   Re-run this whenever `strategy.hpp` / `pairs_strategy.hpp` change.
3. Run any strategy script, e.g. `python3 test_basic_mr.py`

### Strategies

None of these beat buy & hold over the periods tested. Kept anyway, because each one either taught a specific lesson or ruled something out.

#### `test_basic_mr.py` — Basic Mean Reversion
Entry when a stock closes >3% below its own SMA(20); exit when price reverts to the SMA. 30-stock universe, no momentum gating, max 5 concurrent positions, cash split evenly across open slots, no stop-loss/time-stop. The simplest rule in the repo, and it produced the best single-period number: **Sharpe 1.14** in the C++ engine ($16,635 from $10,000), 1.34 in the original pure-Python prototype. The ~0.2 gap between the two isn't a strategy difference — it's traced to position-sizing order (Python sizes all of a day's entries off one fixed daily cash snapshot; C++ resizes after each fill) and where a few end-of-window forced liquidations land in the equity curve. Take the C++ number as the real one, since that's what actually runs. Both numbers are single-period and in-sample — see the next entry before trusting either.

#### `test_mr_py.py` — Walk-Forward Validation of the Same Rule
Takes the exact same basic-MR rule and stops pretending a single 2-year window is meaningful. For each test year 2018–2025, grid-searches stop-loss (5–22%) and time-stop (10–30 days) on all prior years, then trades the winning config on the held-out year:

| Test Year | Sharpe | Return |
| :--- | :--- | :--- |
| 2018 | -1.12 | -19.8% |
| 2019 | +0.63 | +13.6% |
| 2020 | -0.10 | -5.6% |
| 2021 | +0.87 | +20.1% |
| 2022 | -0.66 | -15.5% |
| 2023 | +0.34 | +9.2% |
| 2024 | +1.04 | +24.9% |
| 2025 | +1.20 | +36.4% |

Stitched across all 8 years: **Sharpe 0.15**, roughly tied with buy & hold. The swing from -1.12 to +1.20 isn't noise in the usual sense — it tracks market regime (down/choppy years punish dip-buying, calm bull years reward it) and each fold's "best" stop-loss lands somewhere between 8% and 22% with no consistent value, which is itself evidence the grid search is fitting each window's noise rather than finding one real parameter.

#### `test_mr.py` — Mean Reversion + Momentum Filter
28–30 stock universe (Tech/Healthcare/Financials/Consumer/Industrials), gated to the top-15 by ROC63/126/252 momentum rank before a SMA(2) < SMA(8)×0.99 entry fires. Exits on profit target, 3% stop, or 5-bar time stop. Roughly ten variants were tuned:

| Iteration | Sharpe |
| :--- | :--- |
| Momentum filter ON (buggy eligibility) | 0.76 |
| Momentum filter OFF | 0.55 |
| Eligibility bug fixed + ATR(14) stop/time-stop | 0.51 |
| + ATR(14) profit target | 0.50 |
| 2021–2023 window (incl. 2022 bear market) | -0.62 |
| + volatility-normalized entry | 0.39 / -0.31 (2024–26 / 2021–23) |
| + ~20bps round-trip transaction costs | 0.22 / -0.52 |

Current build: **Sharpe 0.23**. Across every variant and both regimes tested, Sharpe ranged -0.6 to +0.8 and never beat buy & hold — the momentum filter tightens the return distribution somewhat but doesn't create edge, it trades return for smoothness.

#### `test_rsi.py` — RSI-Ranked Mean Reversion
Same universe and engine as above, but candidates are ranked by RSI(5) each day so the most-oversold stock gets first claim on an open slot instead of iterating in a fixed order. **Sharpe 0.17** — the ranking change alone doesn't beat the plain version.

#### `test_pairs.py` — Statistical Arbitrage / Pairs Trading
Engle-Granger cointegration test over a formation period estimates a hedge ratio between two stocks; trades a rolling z-score of their spread, market-neutral (long one leg, short the other). This one took several real iterations to get right, and each iteration is worth knowing about on its own — see "Notable bugs" below. Current state: 66 candidate pairs (sub-industry + economically-motivated cross-sector, e.g. Visa/Mastercard, chipmakers vs. the hyperscalers whose capex funds them), FDR-corrected for the 66 hypotheses tested, formation period 2015–2024. Four pairs survive: V/MA, V/WMT, MA/WMT, AMZN/CRM — worth noting the first three are all pairwise combinations of the same 3 stocks, not 3 independent relationships. **Sharpe 0.49**, still behind buy & hold, but the only strategy here where the underlying statistical relationship is provably not noise.

### Notable bugs found along the way

The actual engineering value in this repo is here, not in the Sharpe column above:

- **Cash hoarding**: position sizing used 10% of *remaining* cash per trade, leaving >60% idle. Fixing it to split cash evenly across open slots took Sharpe 0.30 → 0.84 on the original 6-stock universe — a pure accounting fix, not a better idea.
- **Spurious cointegration**: the first version of `test_pairs.py` tested 86 candidate pairs at a flat p<0.05 with no multiple-testing correction. Applying Benjamini-Hochberg correction dropped all 5 "significant" pairs to zero — they were noise. Pair selection was rebuilt around economically-motivated candidates instead of blind sector combinatorics (see above).
- **Idle capital, again**: the pairs engine divided cash by a fixed 5-slot cap regardless of how many pairs were actually found — with 2 pairs, 60% of capital sat unused. Scaling the divisor to the real pair count roughly doubled position sizes.
- **Silent inverse-pair rejection**: the C++ pairs engine computed negative share counts for any inverse (negative hedge-ratio) relationship and just refused to trade it, with no error. Fixed to size and sign both legs from `|hedge_ratio|` instead of assuming a positive one.
- **Self-dampening stop-loss**: the rolling 30-day z-score window used for entries/exits also fed the stop-loss threshold, so a genuinely breaking pair's rolling stdev inflated *with* the divergence, delaying the stop exactly when it mattered. Widened to 60 days.
- **Python vs. C++ parity**: porting `test_basic_mr.py` from Python to C++ dropped its Sharpe from 1.34 to 1.14 with identical strategy logic — traced to position-sizing timing and end-of-window liquidation order, not a real behavioral difference.
