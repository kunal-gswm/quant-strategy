# Trend Pullback Strategy
# Walk-Forward Validation Report

## 1. Executive Summary

This report presents the results of an expanding-window walk-forward validation
of the frozen Trend Pullback strategy on a 184-stock NSE universe.

**Key Findings:**
- Total OOS trades: 191
- OOS win rate: 48.7%
- OOS mean R: 0.338
- OOS net P&L: Rs.61,572.29
- OOS profit factor: 1.62
- OOS max drawdown: Rs.9,897.02
- Profitable test years: 5/5 (100%)

**Research Classification: Promising but Unconfirmed**

## 2. Baseline Strategy

Parameters are frozen. No optimization was performed.

| Parameter | Value |
|-----------|------:|
| EMA period | 50 |
| EMA slope lookback | 5 bars |
| RSI period | 14 |
| RSI reclaim level | 40.0 |
| ATR period | 14 |
| Stop | 1.5 × ATR |
| Target | 2.0R |
| Direction | Long only |
| Entry | Next bar Open |

## 3. Previous Validation Results

From the prior validation phase (2020-2025 pooled backtest):
- 221 trades, 46.61% win rate
- Rs.71,285.61 net P&L
- Positive under 2x and 3x cost assumptions
- 2025 Final OOS: 28 trades, 50% win rate, Rs.10,885 net P&L, 1.75 PF
- Classification: Promising but Unconfirmed

## 4. Walk-Forward Methodology

Expanding-window walk-forward validation with frozen parameters.

The strategy parameters remain **unchanged** across all windows.
The "training" period is NOT used to optimize parameters — it is simply
the historical information available before each test period.

Each test period is completely isolated from other test periods when
calculating performance.

Data period: 2019-01-01 to 2025-12-31 (2019 = indicator warm-up)

## 5. Test Windows

| Window | Train Period | Test Period |
|--------|:-------------|:------------|
| 1 | 2019-01-01 → 2020-12-31 | **2021** |
| 2 | 2019-01-01 → 2021-12-31 | **2022** |
| 3 | 2019-01-01 → 2022-12-31 | **2023** |
| 4 | 2019-01-01 → 2023-12-31 | **2024** |
| 5 | 2019-01-01 → 2024-12-31 | **2025** |

## 6. Walk-Forward Results

| Test Year | Trades | Win Rate | Mean R | Net P&L | Profit Factor |
|----------:|-------:|--------:|------:|--------:|--------------:|
| 2021 | 59 | 44.1% | 0.265 | Rs.14,342.67 | 1.42 |
| 2022 | 27 | 51.9% | 0.112 | Rs.3,371.08 | 1.28 |
| 2023 | 29 | 41.4% | 0.112 | Rs.2,971.69 | 1.16 |
| 2024 | 48 | 56.2% | 0.645 | Rs.30,001.55 | 2.49 |
| 2025 | 28 | 50.0% | 0.419 | Rs.10,885.31 | 1.75 |


## 7. Aggregate OOS Performance

| Metric | Value |
|--------|------:|
| Total OOS trades | 191 |
| Total OOS wins | 93 |
| Total OOS losses | 98 |
| OOS win rate | 48.7% |
| OOS mean R | 0.338 |
| OOS median R | -0.650 |
| OOS expectancy | Rs.322.37 |
| OOS profit factor | 1.62 |
| OOS gross P&L | Rs.70,866.18 |
| OOS costs | Rs.9,293.89 |
| OOS net P&L | Rs.61,572.29 |
| OOS max drawdown | Rs.9,897.02 |
| Profitable test years | 5 |
| Losing test years | 0 |
| % test years profitable | 100% |

## 8. OOS Yearly Stability

| Test Year | Trades | Win Rate | Mean R | Net P&L | Profit Factor |
|----------:|-------:|--------:|------:|--------:|--------------:|
| 2021 | 59 | 44.1% | 0.265 | Rs.14,342.67 | 1.42 |
| 2022 | 27 | 51.9% | 0.112 | Rs.3,371.08 | 1.28 |
| 2023 | 29 | 41.4% | 0.112 | Rs.2,971.69 | 1.16 |
| 2024 | 48 | 56.2% | 0.645 | Rs.30,001.55 | 2.49 |
| 2025 | 28 | 50.0% | 0.419 | Rs.10,885.31 | 1.75 |


**Stability Metrics:**
- Mean annual OOS P&L: Rs.12,314.46
- Median annual OOS P&L: Rs.10,885.31
- Std deviation annual OOS P&L: Rs.11,025.66
- Best OOS year: 2024
- Worst OOS year: 2023

*Note: These are descriptive statistics only and should not be interpreted
as evidence of future performance.*

## 9. OOS Regime Analysis

| Regime | Trades | Win Rate | Mean R | Net P&L | Profit Factor | Reliable |
|--------|-------:|--------:|------:|--------:|--------------:|----------|
| BEAR | 2 | 100.0% | 1.940 | Rs.3,808.71 | inf | **No (<20)** |
| BULL | 169 | 50.9% | 0.391 | Rs.62,833.12 | 1.75 | Yes |
| SIDEWAYS | 20 | 25.0% | -0.272 | Rs.-5,069.54 | 0.65 | Yes |


*Regimes with fewer than 20 trades should not be interpreted as reliable evidence.*

## 10. OOS Sector Analysis

| Sector | Trades | Win Rate | Mean R | Net P&L | Profit Factor | Sample |
|--------|-------:|--------:|------:|--------:|--------------:|--------|
| Automobile | 20 | 45.0% | 0.332 | Rs.6,612.54 | 1.68 | Adequate |
| Banking & Finance | 38 | 50.0% | 0.296 | Rs.11,169.95 | 1.56 | Adequate |
| Capital Goods | 14 | 50.0% | 0.449 | Rs.6,424.33 | 1.93 | Adequate |
| Cement | 10 | 60.0% | 0.617 | Rs.5,674.51 | 2.56 | Adequate |
| Chemicals | 11 | 54.5% | 0.569 | Rs.5,496.97 | 2.04 | Adequate |
| Consumer Durables | 9 | 55.6% | 0.562 | Rs.4,189.52 | 2.02 | Low (<10) |
| FMCG | 10 | 30.0% | -0.180 | Rs.-1,548.76 | 0.79 | Adequate |
| IT | 12 | 58.3% | 0.492 | Rs.5,779.86 | 2.31 | Adequate |
| Infrastructure | 12 | 50.0% | 0.438 | Rs.4,888.63 | 1.81 | Adequate |
| Media | 4 | 25.0% | -0.322 | Rs.-1,222.51 | 0.61 | Low (<10) |
| Metals & Mining | 13 | 46.2% | 0.086 | Rs.974.47 | 1.13 | Adequate |
| Oil & Gas | 6 | 50.0% | 0.433 | Rs.2,627.56 | 1.82 | Low (<10) |
| Pharma & Healthcare | 14 | 64.3% | 0.864 | Rs.11,490.70 | 3.23 | Adequate |
| Power | 7 | 28.6% | -0.194 | Rs.-1,373.76 | 0.74 | Low (<10) |
| Real Estate | 8 | 37.5% | 0.080 | Rs.669.69 | 1.13 | Low (<10) |
| Telecom | 2 | 50.0% | 0.388 | Rs.740.27 | 1.67 | Low (<10) |
| Textiles | 1 | 0.0% | -1.026 | Rs.-1,021.67 | 0.00 | Low (<10) |


*Sectors flagged as "Low (<10)" have insufficient sample size for reliable conclusions.*

## 11. OOS Stock Analysis

See: `results/walk_forward_stock_summary.csv`

- Stocks with positive OOS P&L: 60
- Stocks with negative OOS P&L: 54
- Stocks with zero trades: 70
- Average trades per stock/year: 0.34

*Individual stock results with very small samples should not be used to draw conclusions.*

## 12. Execution Audit

See: `results/execution_audit_v2.csv`

Every trade has been classified into one or more categories:
NORMAL_STOP, NORMAL_TARGET, GAP_THROUGH_STOP, GAP_THROUGH_TARGET,
ENTRY_SLIPPAGE, EXIT_SLIPPAGE, TRANSACTION_COST, INTEGER_POSITION_SIZE,
END_OF_DATA, INTRABAR_AMBIGUITY, OTHER.

Execution audit result: **PASS**

## 13. Look-Ahead Bias Audit

See: `results/lookahead_audit.md`

All checks passed with the following caveats:
- Survivorship bias remains unresolved
- Yahoo Finance corporate action adjustments are assumed correct

## 14. Cost Sensitivity

| Multiplier | Trades | Net P&L | Mean R | Profit Factor | Max DD |
|:----------:|-------:|--------:|------:|--------------:|-------:|
| 1.0x | 191 | Rs.61,572.29 | 0.338 | 1.62 | Rs.9,897.02 |
| 2.0x | 191 | Rs.52,278.41 | 0.288 | 1.50 | Rs.10,886.54 |
| 3.0x | 191 | Rs.42,984.52 | 0.237 | 1.40 | Rs.11,876.06 |


## 15. Parameter Stability

| Parameter | Value | Baseline | Trades | Win Rate | Mean R | Net P&L | PF |
|-----------|------:|:--------:|-------:|--------:|------:|--------:|----:|
| rsi_reclaim_level | 35.0 |  | 10 | 70.0% | 0.624 | Rs.6,122 | 3.74 |
| rsi_reclaim_level | 40.0 | **✓** | 191 | 48.7% | 0.338 | Rs.61,572 | 1.62 |
| rsi_reclaim_level | 45.0 |  | 1382 | 42.2% | 0.175 | Rs.228,442 | 1.28 |
| ema_period | 40.0 |  | 60 | 50.0% | 0.404 | Rs.23,817 | 1.79 |
| ema_period | 50.0 | **✓** | 191 | 48.7% | 0.338 | Rs.61,572 | 1.62 |
| ema_period | 60.0 |  | 434 | 42.4% | 0.154 | Rs.65,062 | 1.26 |
| stop_atr_multiple | 1.25 |  | 191 | 51.8% | 0.435 | Rs.80,633 | 1.86 |
| stop_atr_multiple | 1.5 | **✓** | 191 | 48.7% | 0.338 | Rs.61,572 | 1.62 |
| stop_atr_multiple | 1.75 |  | 189 | 48.1% | 0.315 | Rs.58,431 | 1.60 |
| reward_risk_multiple | 1.5 |  | 191 | 54.5% | 0.269 | Rs.49,056 | 1.56 |
| reward_risk_multiple | 2.0 | **✓** | 191 | 48.7% | 0.338 | Rs.61,572 | 1.62 |
| reward_risk_multiple | 2.5 |  | 189 | 42.9% | 0.347 | Rs.62,961 | 1.58 |


The purpose is to determine whether the baseline sits inside a stable
region, not to select the best parameters.

## 16. OOS Monte Carlo

10,000 simulations using randomized trade order (shuffle) on OOS trades only.

| Metric | Value |
|--------|------:|
| Median final P&L | Rs.61,572.29 |
| 5th percentile P&L | Rs.61,572.29 |
| 95th percentile P&L | Rs.61,572.29 |
| Median max drawdown | Rs.8,874.78 |
| 95th percentile max DD | Rs.14,028.26 |
| P(negative final P&L) | 0.0% |

*This does NOT represent the probability that the real strategy will lose money.
It only describes the distribution generated by resampling the observed OOS trades.*

## 17. Bootstrap Confidence Intervals

10,000 bootstrap samples, seed=42, 95% confidence intervals.

| Statistic | Point Estimate | 95% CI |
|-----------|:--------------:|:------:|
| Mean R | 0.338 [0.134, 0.544] |
| Win Rate | 48.7% [41.4%, 56.0%] |
| Expectancy | Rs.322.37 [124.19, 521.58] |

## 18. Survivorship Bias

**Status: UNRESOLVED**

The current universe uses 184 stocks that are currently listed
and trading on the NSE. Historical index membership data is not available
in the repository.

Required: Date-effective historical NIFTY 500 constituent membership.

Impact: Current results remain subject to survivorship bias.

## 19. Limitations

1. **Survivorship bias** — the universe uses only currently-active stocks.
2. **Daily bars only** — intrabar execution order is assumed, not verified.
3. **Yahoo Finance data** — corporate action adjustments may not be perfect.
4. **Small sample size** — 191 OOS trades is a limited sample.
5. **Single strategy** — no comparison against null hypothesis / random baseline.
6. **No portfolio-level analysis** — trades are analysed individually, not as a portfolio.
7. **Transaction costs assumed** — actual costs may differ from the model.
8. **No market impact** — position sizes are small enough to assume no impact.

## 20. Reproducibility

```
py run_walk_forward.py
```

Configuration saved in: `results/walk_forward_configuration.json`
Random seed: 42

## 21. Research Conclusion

**Classification: Promising but Unconfirmed**

The strategy shows consistent positive OOS performance across walk-forward test windows with 5 out of 5 test years profitable.

This classification is based on:
- Walk-forward OOS performance across 5 test windows
- 191 total OOS trades
- OOS profit factor of 1.62
- Cost robustness testing at 1x, 2x, and 3x costs
- Parameter stability analysis
- Bootstrap confidence intervals

**This is not an investment recommendation.** The strategy has not been proven
to be profitable in the future. Results are subject to survivorship bias and
other limitations described above.
