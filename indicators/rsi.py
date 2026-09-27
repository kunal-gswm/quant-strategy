import numpy as np
import pandas as pd

def wilder_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    
    avg_gain = pd.Series(np.nan, index=close.index)
    avg_loss = pd.Series(np.nan, index=close.index)
    
    if len(close) <= period:
        return pd.Series(np.nan, index=close.index)
        
    avg_gain.iloc[period] = gain.iloc[1:period + 1].mean()
    avg_loss.iloc[period] = loss.iloc[1:period + 1].mean()
    
    for i in range(period + 1, len(close)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period
        
    rsi = pd.Series(np.nan, index=close.index)
    for i in range(period, len(close)):
        if avg_loss.iloc[i] == 0:
            rsi.iloc[i] = 100.0  # explicit branch — Section 5.2
        else:
            rs = avg_gain.iloc[i] / avg_loss.iloc[i]
            rsi.iloc[i] = 100.0 - (100.0 / (1.0 + rs))
            
    return rsi
