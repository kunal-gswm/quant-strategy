"""Market regime classification using Nifty 50 as the benchmark.

Regime rules are defined BEFORE looking at strategy results (Section 11).

Trend regime (mutually exclusive):
  BULL     : Nifty 50 close > 200-day SMA  AND  200-day SMA > SMA[20 days ago]
  BEAR     : Nifty 50 close < 200-day SMA  AND  200-day SMA < SMA[20 days ago]
  SIDEWAYS : everything else

Volatility regime (independent of trend):
  HIGH_VOL : 30-day realized volatility > rolling 1-year median volatility
  LOW_VOL  : 30-day realized volatility <= rolling 1-year median volatility
"""

import numpy as np
import pandas as pd


def classify_regimes(nifty: pd.DataFrame) -> pd.DataFrame:
    """Given a DataFrame with at least a 'close' column indexed by date,
    return a DataFrame with columns: trend_regime, vol_regime."""

    close = nifty["close"].copy()

    # --- Trend regime --------------------------------------------------------
    sma200 = close.rolling(200).mean()
    sma200_lag = sma200.shift(20)

    trend = pd.Series("SIDEWAYS", index=close.index)
    trend[(close > sma200) & (sma200 > sma200_lag)] = "BULL"
    trend[(close < sma200) & (sma200 < sma200_lag)] = "BEAR"

    # --- Volatility regime ---------------------------------------------------
    log_ret = np.log(close / close.shift(1))
    realized_vol_30 = log_ret.rolling(30).std() * np.sqrt(252)
    rolling_median_vol = realized_vol_30.rolling(252).median()

    vol = pd.Series("LOW_VOL", index=close.index)
    vol[realized_vol_30 > rolling_median_vol] = "HIGH_VOL"

    return pd.DataFrame({
        "trend_regime": trend,
        "vol_regime": vol,
        "sma200": sma200,
        "realized_vol_30d": realized_vol_30,
    }, index=close.index)


def tag_trades_with_regime(trades: pd.DataFrame,
                           regime_df: pd.DataFrame) -> pd.DataFrame:
    """Attach trend_regime and vol_regime columns to a trade ledger
    based on each trade's signal_timestamp."""
    trades = trades.copy()
    sig_dates = pd.to_datetime(trades["signal_timestamp"]).dt.normalize()

    trend_map = regime_df["trend_regime"]
    vol_map   = regime_df["vol_regime"]

    trades["trend_regime"] = sig_dates.map(trend_map).values
    trades["vol_regime"]   = sig_dates.map(vol_map).values

    return trades
