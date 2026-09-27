import numpy as np
import pandas as pd

def wilder_atr(candles: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = candles["high"], candles["low"], candles["close"]
    prev_close = close.shift(1)
    
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    
    atr = pd.Series(np.nan, index=candles.index)
    if len(candles) <= period:
        return atr
        
    atr.iloc[period] = tr.iloc[1:period + 1].mean()
    for i in range(period + 1, len(candles)):
        atr.iloc[i] = (atr.iloc[i - 1] * (period - 1) + tr.iloc[i]) / period
        
    return atr
