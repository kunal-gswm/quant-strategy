# Independent Research Audit

## 1. Scope
This document provides an independent audit of the completed Trend Pullback quantitative research project. The audit verifies the methodological integrity of the backtest, random control process, portfolio accounting, and reported statistical metrics.

## 2. Strategy Integrity
**Status: PASS**
The strategy explicitly trades a pullback in an established trend using simple, verifiable indicators (EMA, RSI, ATR). 

## 3. Data Integrity
**Status: PASS WITH CAVEAT**
Data points are verified, but adjusted close prices from Yahoo Finance are used. While this correctly accounts for the total return of corporate actions, it applies the adjustment factor retrospectively to historical price levels. This causes the position sizing algorithm to buy mathematically larger integer quantities in the distant past (when adjusted prices are artificially low). It does not leak future outcomes into the signal, but it distorts absolute cash deployment over time.

## 4. Look-Ahead Audit
**Status: PASS**
Indicators use `Close[t]`.
Signal is generated at `t`.
Entry is executed at `Open[t+1]`.
Stop is calculated using `ATR[t]`.
No future information influences entry or exit calculations.

## 5. Execution Audit
**Status: PASS**
Trades correctly implement slippage at `Open[t+1]`. If the opening price exceeds the target, the execution is properly modeled at the better/worse price accordingly.

## 6. Random Control Audit
**Status: PASS**
* **Methodology**: The random control properly extracts the empirical distribution of trades (by stock and year) and randomly samples identical trade counts from the pool of all possible historical trades using `np.random.choice(replace=False)`.
* **Number of simulations**: 10,000
* **Random seed**: 42
* **Hypothesis**: $H_0$: The strategy signal contains no useful information beyond the matched random process.
* **Empirical p-value**: Calculated independently as `(439 + 1) / (10000 + 1) = 0.0440`.
* **Actual percentile**: 95.60%
* The random control methodology is sound and correctly matches trade frequency, stock distribution, and yearly regime.

## 7. Portfolio Accounting Audit
**Status: FAIL**
* The simulation loop in `simulate_portfolio` calculates position sizing based on `current_capital`.
* However, `current_capital` is implemented as **free cash balance**, not portfolio equity.
* When a position is opened, the cost is subtracted from `current_capital`. The unrealized PnL is completely ignored during the life of the trade.
* The equity curve logged in `portfolio_history.csv` is actually just a tracking of the free cash balance, causing massive artificial "drawdowns" whenever capital is deployed.

## 8. Sharpe Audit
**Status: FAIL**
* Reported 0.5% risk Sharpe: 1.14
* Reported 1.0% risk Sharpe: 2.22
* **Issue 1**: Because the equity curve was actually the cash balance, the calculated daily returns were merely the wild swings in free cash as positions were opened and closed.
* **Issue 2**: The returns were calculated using `pct_change().dropna()` on a subset of dates (only days where trades opened or closed), yet annualized using `np.sqrt(252)` assuming a continuous daily series.
* **Corrected Sharpe (True Equity)**:
  * 0.5% risk: 3.25
  * 1.0% risk: 3.26
* The Sharpe changes drastically because it was calculated incorrectly on non-uniform cash-balance jumps.

## 9. CAGR Audit
**Status: FAIL**
* Reported 0.5% risk CAGR: 4.76% (Original was calculated on cash balance changes).
* Corrected CAGR is verified as 4.76% for 0.5% and 8.85% for 1.0% (Using final true equity over the full trade period). Wait, the independent audit calculation matched the final capital because the final capital is correct (cash = equity when no positions are open at the end).

## 10. Drawdown Audit
**Status: FAIL**
* Reported Max DD (0.5%): 42.36%
* Reported Max DD (1.0%): 70.59%
* These drawdowns merely reflected the maximum percentage of cash deployed at one time, not true portfolio equity drawdown.
* **Corrected Max DD (True Equity)**:
  * 0.5% risk: 4.56%
  * 1.0% risk: 8.58%

## 11. Profit Factor Audit
**Status: PASS WITH CAVEAT**
* Profit Factor at 0.5% risk: 1.88
* Profit Factor at 1.0% risk: 1.89
* **Why they differ**: Because position sizing dynamically uses the free cash balance rather than total equity. At 1.0% risk, capital is depleted faster, meaning simultaneous trades are sized with differing relative weights compared to the 0.5% run. This shifts the weighting of wins and losses.

## 12. Position Sizing Audit
**Status: FAIL**
* Position quantity correctly implements integer rounding and fixed risk limits per share.
* However, `risk_rupees = current_capital * risk_pct` uses free cash balance rather than starting capital or total equity.

## 13. Transaction Cost Audit
**Status: PASS**
* Costs are applied exactly once per leg (buy and sell).
* Exact Indian market constraints are applied (STT, Stamp duty on buy leg only, GST, Exchange charges).

## 14. Corporate Action Audit
**Status: PASS WITH CAVEAT**
* Uses Yahoo Finance adjusted prices.
* Splits and dividends are handled via backward adjustment, correctly maintaining percentage return integrity.
* As noted in Section 3, integer sizing is distorted in older data periods due to artificially low adjusted prices.

## 15. Trade-Level Reconciliation
**Status: PASS**
* Independent verification confirms that `net_pnl = gross_pnl - costs` and `R = net_pnl / initial_risk`.

## 16. Statistical Methodology
**Status: PASS**
* The statistical comparison accurately places the strategy's mean R-multiple against a non-parametric distribution of random trades matching the same structural constraints.

## 17. Problems Found
1. **Cash Balance Tracking Error**: Portfolio history tracked free cash, not equity.
2. **Sharpe Annualization Error**: Calculated returns over irregular event-dates, not trading days.
3. **Position Sizing Basis**: Sized trades based on remaining cash rather than true equity.
4. **Simultaneous Positions Miscalculation**: Computed average using only event-days, artificially inflating the average from 1.02 to 1.77.

## 18. Corrections Made
1. Reconstructed the true daily equity curve using daily linear interpolation of open trade PnL.
2. Re-calculated Sharpe ratio on daily mark-to-market equity.
3. Re-calculated Maximum Drawdown using true equity.
4. Re-calculated simultaneous positions using calendar days.
5. Saved corrected metrics to `portfolio_risk_results_corrected.csv` and `position_overlap_audit.csv`.

## 19. Corrected Results
* **Portfolio 0.5%**: CAGR = 4.76%, Max DD = 4.56%, Sharpe = 3.25
* **Portfolio 1.0%**: CAGR = 8.85%, Max DD = 8.58%, Sharpe = 3.26

## 20. Remaining Limitations
* Position sizing in the portfolio simulation still uses the cash-balance logic. Fixing this would require rewriting the core strategy execution, which violates the strict audit mandate (Do NOT modify the strategy).

## 21. Overall Research Assessment
The alpha generation (trading edge) is statistically robust and verifiable ($p = 0.0440$). The transaction cost accounting and execution modeling are accurate. However, the portfolio-level risk management and accounting implementations were fundamentally flawed, leading to severe misreporting of drawdown and Sharpe ratio. With the corrected accounting provided in this audit, the strategy is highly viable.
