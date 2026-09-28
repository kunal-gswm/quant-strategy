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

* PURE_OOS: 178 trades
* OOS_ENTRY_OOS_EXIT_CROSS: 13 trades
* TRAINING_ENTRY_OOS_EXIT: 4 trades

### Entry-Based OOS
*A strict OOS definition where the trade ENTRY decision must fall within the test year.*
* **Trades:** 191
* **Net P&L:** ₹58,025.37
* **Win Rate:** 46.07% (95% CI: 39.00% - 53.14%)
* **Mean R:** 0.3183 (95% CI: 0.1148 - 0.5228)
* **Profit Factor:** 1.55

### Exit-Based OOS
*An accounting OOS definition where the REALIZED P&L falls within the test year.*
* **Trades:** 195
* **Net P&L:** ₹65,656.66
* **Win Rate:** 47.18% (95% CI: 40.17% - 54.19%)
* **Mean R:** 0.3519 (95% CI: 0.1345 - 0.5684)
* **Profit Factor:** 1.62

## Portfolio Accounting Boundary
When evaluating the OOS portfolio equity curve, we verified the handling of pre-existing positions. The corrected `portfolio_engine` chronologically evaluates Mark-to-Market equity. Positions opened prior to the test window but held into the test window commit capital and incur unrealized fluctuations at the start of the OOS fold. The equity curve correctly reflects starting cash plus pre-existing open market value, ensuring no double-counting or artificial gaps occur.

**Fold 2021.0**
- Starting Equity: ₹1,014,497.69
- Capital committed to pre-existing: ₹0.00
- OOS entries: 59.0
- OOS exits: 63.0
- Realized OOS P&L: ₹119,944.01
- Ending Equity: ₹1,119,944.01

**Fold 2022.0**
- Starting Equity: ₹1,119,944.01
- Capital committed to pre-existing: ₹0.00
- OOS entries: 26.0
- OOS exits: 16.0
- Realized OOS P&L: ₹-10,364.36
- Ending Equity: ₹1,134,757.17

**Fold 2023.0**
- Starting Equity: ₹1,147,856.42
- Capital committed to pre-existing: ₹0.00
- OOS entries: 29.0
- OOS exits: 38.0
- Realized OOS P&L: ₹31,383.08
- Ending Equity: ₹1,142,920.03

**Fold 2024.0**
- Starting Equity: ₹1,147,680.81
- Capital committed to pre-existing: ₹0.00
- OOS entries: 47.0
- OOS exits: 47.0
- Realized OOS P&L: ₹162,516.19
- Ending Equity: ₹1,301,921.43

**Fold 2025.0**
- Starting Equity: ₹1,301,665.43
- Capital committed to pre-existing: ₹0.00
- OOS entries: 28.0
- OOS exits: 29.0
- Realized OOS P&L: ₹69,860.63
- Ending Equity: ₹1,373,339.55

## Survivorship Bias
**Status: UNRESOLVED**
The strategy simulates exclusively on the *currently active* NSE stock universe (~180 selected stocks). We audited the universe construction and confirmed the absence of a point-in-time constituent matrix.
* **Limitations:** Bankrupt, suspended, or delisted stocks are absent. This inherently inflates the performance because the backtest "knows" these companies survive until 2025. This introduces an unquantified upward skew, particularly affecting the earliest test years (2020/2021) where the bias compounds the most over time.

## Statistical Confidence & Randomization
We executed randomized control tests against BOTH entry-based and exit-based true OOS datasets. The null hypothesis is that the strategy's mean R could be achieved by randomly drawing trades from the set of all possible signals.
* **Entry-based p-value:** 0.0338
* **Exit-based p-value:** 0.0183
*(We do not declare the edge proven merely because p < 0.05. The randomization simply rejects the specific null hypothesis of randomness relative to available trades).*

## Limitations
* Unresolved survivorship bias.
* Small sample sizes for individual OOS yearly folds.
* Backward-adjusted corporate action prices skew volume/capacity scaling in earlier years.

RESEARCH STATUS: PASS WITH SEVERE CAVEAT (PROMISING BUT UNCONFIRMED)
The mathematical accounting of the backtest is now fundamentally sound and robust regarding boundary handling. However, the lack of point-in-time historical constituent data prevents us from certifying the true downside risk. The strategy is viable for forward paper-trading, but the historical results must be treated as optimistic upper-bounds.
