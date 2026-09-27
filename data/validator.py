import pandas as pd

class DataValidator:
    def validate(self, df: pd.DataFrame):
        rejections = []
        clean = df.copy()
        
        # Section 5.6 Invalid OHLC handling
        invalid_high_low = clean["high"] < clean["low"]
        invalid_high_open = clean["high"] < clean["open"]
        invalid_high_close = clean["high"] < clean["close"]
        invalid_low_open = clean["low"] > clean["open"]
        invalid_low_close = clean["low"] > clean["close"]
        
        negative_open = clean["open"] < 0
        negative_high = clean["high"] < 0
        negative_low = clean["low"] < 0
        negative_close = clean["close"] < 0
        negative_vol = clean["volume"] < 0
        
        zero_open = clean["open"] == 0
        zero_high = clean["high"] == 0
        zero_low = clean["low"] == 0
        zero_close = clean["close"] == 0

        invalid = (invalid_high_low | invalid_high_open | invalid_high_close |
                   invalid_low_open | invalid_low_close |
                   negative_open | negative_high | negative_low | negative_close | negative_vol |
                   zero_open | zero_high | zero_low | zero_close)
        
        if invalid.any():
            rejections = clean[invalid].copy()
            clean = clean[~invalid]
            
        if clean.index.duplicated().any():
            raise ValueError("Duplicate timestamps found")
            
        return clean, rejections
