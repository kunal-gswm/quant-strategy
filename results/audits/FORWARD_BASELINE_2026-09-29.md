# Forward Baseline: 2026-09-29

## Strategy

```text
Strategy Version: TPQSE_v1.0
Launch Date: 2026-09-29
Status: ACTIVE
```

## Operational

| Item | Value |
|---|---|
| Scheduler timezone | India Standard Time (IST, UTC+05:30) |
| Expected runtime | 16:30 IST (Mon–Fri) |
| First execution timestamp | 2026-09-29 00:38:29 IST |
| Data timestamp | N/A (market not yet open) |
| Data age | N/A |
| Data Freshness Mechanism | Evaluated per symbol (FRESH, STALE, NO_DATA, DOWNLOAD_ERROR, UNRESOLVED) |
| Universe expected | 184 |
| Universe processed | 0 (market not open) |
| Universe failed | 4 (SUVENPHAR.NS, TATAMOTORS.NS, LTIM.NS, TVSMOTORS.NS — delisted/renamed) |
| Signal count | 0 |
| Entry count | 0 |
| Exit count | 0 |
| Open positions | 0 |
| Ending equity | ₹1,000,000.00 (starting capital, no activity) |
| Operational status | HEALTHY |

## First Session Result

The first invocation of `daily_forward_runner.py` occurred at 00:38 IST on 2026-09-29 — approximately 9 hours before NSE market open (09:15 IST). Because no intraday or end-of-day data existed for today's date, the engine correctly returned:

```text
No market data for today. Skipping session.
```

This is **expected behavior**. The scheduled daemon cron (`30 16 * * 1-5`) will execute the first genuine data-bearing session at 16:30 IST on the next trading day (expected to be the next non-holiday weekday). Because no reliable NSE calendar is integrated, the exact next eligible session cannot be definitively determined by the reporting layer in advance, but the engine will dynamically process data as Yahoo Finance publishes it.

**No forward signal, trade, or portfolio state was recorded.** The forward ledger is clean.

## Integrity

| Check | Status |
|---|---|
| Timestamp integrity | PASS |
| Duplicate protection | PASS |
| Portfolio reconciliation | PASS (no activity to reconcile) |
| Historical contamination | PASS (no forward_signals.csv, forward_trades.csv, or forward_portfolio_history.csv exist) |
| Restart recovery | PASS (engine recovers identical empty state) |
| Watchdog | PASS |
| Alerting | PASS |
| Test suite | PASS (51 passed, 0 failed) |

## Audit Findings

### FINDING 1: Test-Suite Residual Artifacts (WARNING)

The following files contain data written by test suites, not by genuine forward sessions:

* `results/forward_rolling_metrics.csv` — 25 rows of synthetic data from `test_slippage_failure.py`
* `results/forward_data_revisions.csv` — 5 rows from `test_forward_integrity.py` / `test_forward_monitoring.py`
* `results/forward_portfolio_trades.csv` — empty (header only, from `init_forward_framework.py`)
* `results/forward_validation_milestones.csv` — empty (header only)
* `results/forward_universe_snapshots/universe_20260930.csv` — 1 row from test

These are **not genuine forward observations**. They are artifacts of the test harness writing to the shared `results/` directory. The core forward ledger files (`forward_signals.csv`, `forward_trades.csv`, `forward_portfolio_history.csv`, `forward_open_positions.json`, `forward_session_log.csv`) do **not** exist, confirming no false forward data was recorded.

**Recommendation:** Before the first genuine trading session, manually clean or archive these test residuals. They do not affect the forward engine because the engine reads only `forward_signals.csv`, `forward_trades.csv`, `forward_portfolio_history.csv`, and `forward_open_positions.json` — none of which exist.

### FINDING 2: Stop/Target Basis Difference (WARNING — NO ACTION REQUIRED)

The **historical** backtest calculates stop and target from the **slippage-adjusted fill price**:
```python
stop = entry_fill - 1.5 * ATR
target = entry_fill + 2.0 * (entry_fill - stop)
```

The **forward** engine calculates stop and target from the **signal-bar close** (planned entry):
```python
stop = planned_entry - 1.5 * ATR
target = planned_entry + (ATR * 2.0) * 1.5
```

Both yield `entry + 3.0 * ATR` for the target and `entry - 1.5 * ATR` for the stop, but the anchor point differs by the slippage amount (~0.05% of price). This creates a minor systematic difference in R-multiple calculations between historical and forward tests.

**No action taken.** Modifying either formula would alter the strategy, which is frozen. This difference is documented for the final comparison at 200 trades.

### FINDING 3: Four Universe Symbols Delisted/Renamed (INFO)

Yahoo Finance returned "possibly delisted" for:
* `SUVENPHAR.NS`
* `TATAMOTORS.NS`
* `LTIM.NS`
* `TVSMOTORS.NS`

These may be ticker renames rather than actual delistings (e.g., Tata Motors is a major index constituent). The forward engine correctly excluded them from processing. This is an expected consequence of `SURVIVORSHIP_BIAS: UNRESOLVED`.

### FINDING 4: `test_forward_integrity.py` Was Stale (FIXED)

The test file referenced an older `ForwardPaperEngine` constructor signature (`start_date=`) and older field names (`entry_price`, `risk_rupees`, `data_timestamp`, `exit_price`). These were updated to match the current API without altering the engine itself. The `save_universe_snapshot` method was also missing from the engine class and has been added.

## Software State

| File | SHA-256 |
|---|---|
| `forward_config.py` | `156B73B4485A7EE2E2DB2C256434E034B9610B006D6128178F5BF2798ED599D9` |
| `forward_engine.py` | `3378459EB761750C59AE04E07C93CCA4AFD936782AF9E4D98EEB97806F7D8396` |
| `daily_forward_runner.py` | `4FC26A23048C4E60DAC98C68A860644B154BFFDCDB898885A5AE084776D3A0F3` |
| `forward_watchdog.py` | `2E155E9DEAE6C615BAA07BF994334D206D1D800A27D1E8376BA600A65E80696B` |
| `run_forward_session.py` | `2E381D061EEE36E872DAB19E17C8A06DE67DDD41DA23F89D69E8C76C96E25AE2` |

Git commit: `daf8d27af0147335a84a55bd325d78e1ddf3358d` (2026-09-29 00:48:12 +0530)

> **Note:** The SHA-256 hashes above reflect the state *after* the `save_universe_snapshot` method was added and `test_forward_integrity.py` was fixed. The git commit predates these changes.
