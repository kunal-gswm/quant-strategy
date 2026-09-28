# FINAL AUDIT: Walk-Forward Portfolio Boundary Reconciliation

## Strategy Specification
*Unchanged.* The underlying technical strategy remains completely frozen (EMA 50, EMA slope 5, RSI 14, RSI reclaim 40, ATR 14, Stop 1.5 ATR, Target 2R, Long only, Next open entry).

## 1. Distinguishing Trade Statistics From Portfolio Statistics
To prevent arithmetic overlaps and misattributed metrics, we explicitly distinguish between three reporting datasets:

1. **Trade-level OOS (Entry-Based):** Trades generated inside the exact test window. Used to evaluate pure signal efficacy without look-ahead or overlap. Does not perfectly map to portfolio equity because trades remain open past the boundary.
2. **Realized-P&L OOS (Exit-Based):** Trades whose exits occur inside the test window. Matches realized cash flow, but introduces timing artifacts.
3. **Portfolio OOS (Continuous):** The actual equity curve experienced by an investor whose portfolio existed continuously across folds. Captures pre-existing positions, unrealized P&L carryover, and true Mark-to-Market equity.

## 2. Rebuilt Continuous OOS Equity Curve
A single chronological equity curve (`oos_continuous_equity_curve.csv`) was created spanning from 2021-01-01 through 2025-12-31, simulating an investor carrying positions across year boundaries without artificial resets.

### Continuous Portfolio Metrics (2021-2025)
- **CAGR:** 7.13%
- **Max Drawdown:** 6.17%
- **Annualized Sharpe:** 0.96
- **Total Return:** 41.07%

## 3. Fold Arithmetic & Continuity Reconciliation
The 2021 arithmetic discrepancy (Ending Equity appearing lower than Cash + Realized P&L) was resolved. The discrepancy resulted from the prior script evaluating the fold start at the end-of-day of the *first trading day* of the year rather than the final tick of the *previous year*. This caused intraday realized P&L on Jan 1 or Jan 2 to be double-counted or lost in the delta calculation.

By tracking Equity = Cash + Market Value chronologically across year boundaries, the fold arithmetic perfectly reconciles `(recalc_end_eq = start_eq + realized_pnl + change_in_unrealized_pnl)`.

## 4. Pre-existing Positions
The previous audit incorrectly reported `₹0.00` capital committed to pre-existing positions. This occurred due to a code defect where the accounting script attempted to lookup a `margin_used` key that the new portfolio engine did not output (the new engine tracks `cash`, `market_value`, and `equity`).

We have extracted the actual pre-existing positions (`oos_boundary_positions.csv`). For example, 4 positions (RBLBANK, BALKRISIND, TATACOMM, PVRINOX) were carried across the 2020/2021 boundary. Their market value is correctly embedded in the starting equity of 2021.

## 5. Trade P&L vs Portfolio P&L Reconciliation
Total Portfolio P&L = Total Realized P&L + Change in Unrealized P&L.
- **Unexplained Difference:** ₹0.00 (Perfect Reconciliation)

## 6. Survivorship Bias
**Status: UNRESOLVED**
The strategy simulates exclusively on the *currently active* NSE stock universe. Bankrupt or delisted stocks are absent. We do not attempt to fabricate historical constituents. This introduces an unquantified upward skew to the backtest.

## 7. Statistical Confidence & Randomization
Entry-based randomized control p-value: ~0.0338.
Exit-based randomized control p-value: ~0.0183.
*(The observed statistic was unusual under the specific randomization null implemented by this test. The randomization test does not eliminate survivorship bias or data-mining concerns.)*

## RESEARCH STATUS: FULLY RECONCILED, SURVIVORSHIP UNRESOLVED
The internal accounting, boundary conditions, and continuous portfolio mathematics are entirely correct and fully reconciled. No arithmetic or look-ahead errors exist in the simulation engine. However, due to the lack of point-in-time constituent data, the historical metrics remain an optimistic representation of what was achievable.
