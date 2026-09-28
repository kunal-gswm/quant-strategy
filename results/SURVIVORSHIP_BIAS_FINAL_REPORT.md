# SURVIVORSHIP BIAS FINAL REPORT

## Current Universe
The existing universe is constructed via a hardcoded Python list of tuples inside `universe.py`. It comprises approximately 180 manually selected mid, large, and small-cap stocks from the National Stock Exchange of India (NSE). These stocks represent *currently active* and liquid companies as of the present day (2025/2026). There is no mechanical or rules-based definition (such as "NIFTY 500 constituents") provided in the code, and no point-in-time constituent logic exists.

## Historical Data Availability
Point-in-time information is completely absent from this repository. `data/historical_universe.py` contains stub code explicitly stating that historical membership data is not available. Furthermore, the dataset utilized by the project is downloaded dynamically via Yahoo Finance (`yfinance`), which inherently does not provide historical index constituents, delisted equities, or proper ticker mapping for acquired companies.

## External Data Sources
We evaluated the following external sources:
* **NSE Indices Archives (niftyindices.com):** The official exchange provides point-in-time constituency only via individual monthly Excel/ZIP reports. 
* **Legacy IndexInclExcl.xls:** An outdated historical tracking file that is no longer reliably updated for all broad indices.
* **Commercial Vendors:** Professional survivorship-bias-free data (e.g., CMIE Prowess, Bloomberg, Refinitiv) requires commercial licensing and is not publicly available for automated download in a standardized format.

Because a rigorous point-in-time mapping across thousands of corporate actions (mergers, delistings, ticker changes) requires substantial proprietary data engineering, no external source was ingested. We determined that randomly downloading fragmented open-source data would violate the strict data integrity rules.

## Survivorship Status
**Status: UNRESOLVED**

## Bias Impact
The magnitude of survivorship bias cannot be quantified from the available data. 

Because the baseline universe consists solely of companies that survived and maintained sufficient liquidity until the present day, any companies that went bankrupt, were suspended, or delisted between 2018 and 2025 are systematically excluded from the backtest. This introduces a structural upward skew to the results (especially in earlier years like 2020 and 2021). We strictly decline to manufacture an arbitrary "bias adjustment" penalty, as estimating the performance of missing stocks using today's losers or fixed penalties is mathematically invalid.

## Strategy Results
Because no valid point-in-time universe exists, the strategy was NOT re-run against a synthetic or estimated universe. The results remain exactly as calculated in the previous continuous portfolio audit (using the frozen strategy rules and the static active universe).

## Remaining Limitations
The following elements remain unresolved:
* **Delisting Data:** Missing completely.
* **Ticker Mapping:** Historical ticker symbol changes are not tracked.
* **Corporate-Event Handling:** Mergers, acquisitions, and demergers are not represented in universe membership.
* **Historical Universe Gaps:** The universe in 2020 was populated with 2025's winners.
