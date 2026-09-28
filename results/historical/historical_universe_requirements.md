Status: BLOCKED

Required dataset:
Date-effective historical NIFTY 500 constituents

Required fields:
date
symbol
membership_start
membership_end

Integration Plan:
1. The historical data would be loaded as a pandas DataFrame containing the date ranges for each constituent.
2. The `get_universe()` function in `universe.py` or a new data loading module would query this dataset to dynamically return the list of valid constituents for any given `date` instead of a static list.
3. During backtesting, the engine will only generate signals or maintain positions for stocks if they are present in the historical universe for the specific evaluation date.
4. When a stock's `membership_end` date is reached, any open positions in that stock would be forcefully exited at the next available market price, simulating delisting or removal from the index.
5. All calculations, including portfolio level metrics, will dynamically filter the universe to prevent any look-ahead bias associated with survivorship bias.
