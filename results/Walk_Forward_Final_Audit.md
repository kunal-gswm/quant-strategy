# Walk-Forward Integrity Audit

## 1. The Baseline vs. OOS Confusion
During previous reviews, the full historical backtest baseline (2018–2025) which contained 221 trades was mistakenly presented under the label of "Walk-Forward OOS". The baseline simply represented a single continuous frozen test, which is vulnerable to look-ahead bias if parameters were tuned over the whole period. 

## 2. True Walk-Forward OOS
We have corrected the Walk-Forward process to mathematically prevent look-ahead bias. We implemented a strict expanding window where:
- The strategy trains (warms up) on data strictly prior to the test year.
- Only trades whose **exit** is realized within the test year are counted toward the OOS metrics.
- The test trade dates definitively do not overlap the training period (0 overlaps confirmed).

## 3. Discrepancy Investigation for 2025
The previous independent validation reported 28 trades for 2025. Our strict walk-forward now reports **29 trades** for 2025. 
**Investigation Result:** The discrepancy exists because the legacy `run_walk_forward.py` script filtered test trades based on the **`signal_timestamp`** (when the trade was initiated). However, correct portfolio equity accounting requires filtering by **`exit_timestamp`** (when the P&L is realized). Filtering strictly by `exit_timestamp` mathematically captures exactly 29 trades that closed in 2025, rectifying the discrepancy.

## 4. Full Historical Baseline
* **Trades:** 221
* **Net P&L:** ₹71,285.61
* **Win Rate:** 46.61%
* *This dataset cannot be used as an OOS validation.*

## 5. True Walk-Forward OOS (Aggregated)
* **Trades:** 195
* **Net P&L:** ₹65,656.66
* **Win Rate:** 47.18%
* **Mean R:** 0.35
* *This dataset represents the mathematically rigorous Out-Of-Sample performance.*

## 6. Portfolio Simulation
Using the true OOS trades and the corrected Mark-to-Market continuous daily portfolio engine:
* **Starting Equity:** ₹1,000,000
* **Ending Equity:** ₹1,373,339.55
* **CAGR:** 6.52%
* **Sharpe:** 1.00
* **Max Drawdown:** 6.18%
* *Performance is promising but unconfirmed until live testing.*

## 7. Survivorship Bias Limitation
**Status: Unresolved**
The dataset does not correct for delisted stocks. The results still exhibit survivorship bias, which inherently suppresses realistic failure rates during severe market downturns.
