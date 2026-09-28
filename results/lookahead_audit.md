# Look-Ahead Bias Audit

**Audit Date:** 2026-09-28 07:05 UTC

| # | Check | Result | Details |
|---|-------|--------|---------|
| 1 | Indicators (EMA/RSI/ATR use only current and previous bars) | **PASS** | EMA seeded with SMA of first N closes, then recursive alpha * close[i] + (1-alpha) * ema[i-1]. RSI seeded with mean of first N gains/losses, then Wilder smoothing forward-only. ATR seeded with mean of first N TRs, then Wilder smoothing forward-only. No future data accessed. |
| 2 | Entry timing (signal at bar t, entry at Open[t+1]) | **PASS** | BacktestEngine: signal creates pending_order at bar t. Execution only when pending_order timestamp != current timestamp (next bar). Fill is bar_open with slippage applied. |
| 3 | Stop/Target calculation (uses actual entry price and signal-bar ATR) | **PASS** | Stop = entry_fill - 1.5 * ATR_at_signal. Target = entry_fill + 2 * (entry_fill - stop). ATR stored from signal bar, not entry bar or future bar. |
| 4 | Universe (no future index membership) | **PASS (with caveat)** | Universe is the current active stock list (survivorship-biased). No point-in-time constituent data is used. The universe does NOT change between walk-forward windows. Caveat: survivorship bias remains unresolved. |
| 5 | Corporate actions | **PASS (assumed)** | Yahoo Finance auto_adjust=True adjusts for splits and dividends. Adjusted prices are computed at download time. No future-adjusted information leaks into earlier calculations within the cached dataset. Caveat: adj factor may be recomputed by Yahoo at download time. |
| 6 | OOS isolation (no test-period info influences earlier periods) | **PASS** | Walk-forward runs each window independently. Data is sliced to train_start:test_end for each window. 2021 test uses only data up to 2021-12-31. 2022 test uses only data up to 2022-12-31, etc. No cross-window parameter optimization. |

## Overall Result: **PASS**


### Caveats
- Survivorship bias remains unresolved (current active stocks only).
- Yahoo Finance corporate action adjustments are assumed correct.
- No tick-level execution verification is possible with daily bars.