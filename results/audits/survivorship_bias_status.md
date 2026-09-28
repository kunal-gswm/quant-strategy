# Survivorship Bias Status

## Status: UNRESOLVED

## Reason
Historical index membership data is not available in the repository.

The current universe consists of 179 stocks that are **currently listed and trading**
on the NSE. Stocks that were delisted, merged, or removed between 2019 and 2025
are NOT included.

## Required Future Dataset
Date-effective historical NIFTY 500 constituent membership, including:
- Entry and exit dates for each constituent
- Delisted and merged companies
- Corporate action history

## Impact
Current results remain subject to survivorship bias. This bias generally
**inflates** backtest performance because surviving stocks are, by definition,
the ones that did not fail.

## Repository Search Results
The following files reference related terms but do not contain actual
historical constituent data:

- `run_expanded.py` (matched: NIFTY)
- `run_validation.py` (matched: NIFTY)
- `run_walk_forward.py` (matched: NIFTY)
- `universe.py` (matched: NIFTY)
- `analysis\regime.py` (matched: NIFTY)
- `data\historical_universe.py` (matched: NIFTY)
- `results\historical_universe_summary.csv` (matched: NIFTY)