import pandas as pd

class TrendPullbackStrategy:
    def __init__(self, cfg):
        self.cfg = cfg

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        ema_now = df["ema50"]
        ema_prior = df["ema50"].shift(self.cfg.slope_bars)
        trend_ok = (ema_now > ema_prior) & (df["close"] > ema_now)
        
        rsi_now = df["rsi14"]
        rsi_prior = df["rsi14"].shift(1)
        reclaim = (rsi_prior < self.cfg.rsi_reclaim_level) & (rsi_now >= self.cfg.rsi_reclaim_level)
        
        is_ready = ema_now.notna() & ema_prior.notna() & rsi_now.notna() & rsi_prior.notna()
        
        return trend_ok & reclaim & is_ready
