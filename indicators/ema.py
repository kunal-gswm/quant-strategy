import numpy as np
import pandas as pd

def wilder_style_ema(close: pd.Series, period: int) -> pd.Series:
    """Standard EMA with alpha = 2/(period+1), seeded with the SMA
    of the first `period` closes. Returns NaN for all bars before
    the seed is available (Section 6, warm-up)."""
    if len(close) < period:
        return pd.Series(np.nan, index=close.index)
        
    alpha = 2.0 / (period + 1)
    ema_values = pd.Series(np.nan, index=close.index)
    
    seed = close.iloc[:period].mean()
    ema_values.iloc[period - 1] = seed
    
    for i in range(period, len(close)):
        prev = ema_values.iloc[i - 1]
        ema_values.iloc[i] = alpha * close.iloc[i] + (1 - alpha) * prev
        
    return ema_values
