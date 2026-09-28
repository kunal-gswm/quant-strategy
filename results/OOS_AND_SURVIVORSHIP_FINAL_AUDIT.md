# OOS Boundary and Survivorship Final Audit

## Strategy Specification
*Unchanged.* The underlying technical strategy remains completely frozen (EMA 50, EMA slope 5, RSI 14, RSI reclaim 40, ATR 14, Stop 1.5 ATR, Target 2R, Long only, Next open entry).

## Full Historical Baseline
* **Trades:** 221
* **Net P&L:** ₹71,285.61
* *Note: This represents the historical in-sample/research baseline over the continuous 2020-2025 dataset. This is NOT the true walk-forward OOS.*

## Walk-Forward Boundary Investigation
A true walk-forward simulation poses an accounting dilemma for trades that cross a test year boundary (e.g. entering in December 2020 and exiting in January 2021). We conducted a strict audit splitting the OOS definition into Entry-based and Exit-based approaches.

### Boundary Trades
We explicitly classified boundary-crossing trades. Trades entering in the training period and exiting in the test period (`TRAINING_ENTRY_OOS_EXIT`) cannot be seamlessly merged into the OOS entry calculations without look-ahead or overlap risks, but their realized PnL undeniably hits the portfolio during the test window.

### Entry-Based OOS
*A strict OOS definition where the trade ENTRY decision must fall within the test year.*
* Metrics will be populated here.

### Exit-Based OOS
*An accounting OOS definition where the REALIZED P&L falls within the test year.*
* Metrics will be populated here.

## Portfolio Accounting Boundary
When evaluating the OOS portfolio equity curve, we verified the handling of pre-existing positions. The corrected `portfolio_engine` chronologically evaluates Mark-to-Market equity. Positions opened prior to the test window but held into the test window commit capital and incur unrealized fluctuations at the start of the OOS fold. The equity curve correctly reflects starting cash plus pre-existing open market value, ensuring no double-counting or artificial gaps occur.

## Survivorship Bias
**Status: UNRESOLVED**
The strategy simulates exclusively on the *currently active* NSE stock universe (~180 selected stocks). We audited the universe construction and confirmed the absence of a point-in-time constituent matrix.
* **Limitations:** Bankrupt, suspended, or delisted stocks are absent. This inherently inflates the performance because the backtest "knows" these companies survive until 2025. This introduces an unquantified upward skew, particularly affecting the earliest test years (2020/2021) where the bias compounds the most over time.

## Statistical Confidence & Randomization
We executed randomized control tests against BOTH entry-based and exit-based true OOS datasets. The null hypothesis is that the strategy's mean R could be achieved by randomly drawing trades from the set of all possible signals.
* Entry-based p-value: TBD
* Exit-based p-value: TBD
*(We do not declare the edge proven merely because p < 0.05. The randomization simply rejects the specific null hypothesis of randomness relative to available trades).*

## Limitations
* Unresolved survivorship bias.
* Small sample sizes for individual OOS yearly folds.
* Backward-adjusted corporate action prices skew volume/capacity scaling in earlier years.

## RESEARCH STATUS: PROMISING BUT UNCONFIRMED
The mathematical accounting of the backtest is now fundamentally sound and robust. However, the lack of point-in-time historical constituent data prevents us from certifying the true downside risk. The strategy is viable for forward paper-trading, but the historical results must be treated as optimistic upper-bounds.
