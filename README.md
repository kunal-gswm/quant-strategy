# TPQSE (Trend Pullback Quantitative Strategy Engine)

TPQSE is a quantitative trading research and execution framework built for the Indian equities market (NSE). 
It features a rigorous historical out-of-sample (walk-forward) validation engine and a strict, fully isolated forward paper-trading daemon.

## Architecture & Structure

The repository is cleanly divided into historical research and forward-testing production environments:

* `forward/` - Production daemon for live paper-trading. Includes the strictly frozen strategy configuration, stateful engine, and daily cron runner.
* `research/` - Historical walk-forward optimization, boundary auditing, and portfolio reconciliation scripts.
* `strategy/` - Core strategy implementation (`TPQSE_v1.0`).
* `data/` - YFinance historical data loader, cache, and validation.
* `indicators/` - Wilder-style technical indicators (EMA, RSI, ATR).
* `execution/` - Friction models (slippage, transaction costs).
* `backtest/` - Core historical event-driven simulation engine.
* `portfolio/` - Portfolio-level accounting and risk-parity sizing.
* `analysis/` & `metrics/` - Post-trade evaluation, monte carlo, and distributions.
* `tests/` - Comprehensive Pytest suite enforcing integrity constraints and isolating production data.
* `results/` - All outputs, split into `historical/`, `forward/`, and `audits/`.

## Running the System

### Tests
To ensure the integrity of the framework and verify that production ledgers are safely isolated, run the full test suite from the root directory:
```bash
python -m pytest -q
```

### Forward Testing
The strategy is currently frozen as `TPQSE_v1.0`. The forward test is **FROZEN AND ACTIVE**.
To execute the daily forward simulation manually (usually run via a post-market cron job):
```bash
python -m forward.runner
```
*Note: The forward runner is idempotent; running it multiple times a day will not duplicate ledger entries.*

### Historical Research
To rerun the historical walk-forward analysis:
```bash
python -m research.walk_forward
```

## Important Disclaimers

1. **Survivorship Bias:** The historical validation suffers from an explicitly documented and UNRESOLVED survivorship bias, as historical delisted symbols could not be fully sourced from the primary data provider. 
2. **Methodology Variance:** Historical entry executions are anchored to the slippage-adjusted fill. Forward executions are anchored to the planned entry bar close.
3. **No Financial Advice:** This repository does not claim that the strategy is profitable, nor is it financial advice. The forward test exists specifically to gather out-of-sample data free from historical lookup bias.
