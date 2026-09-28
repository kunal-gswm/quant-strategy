import pandas as pd
from datetime import timedelta
import yfinance as yf
from forward_config import classify_symbol_failure

def get_symbol_health(df: pd.DataFrame, execution_timestamp: pd.Timestamp) -> dict:
    """Determine the health of a single symbol based on its data."""
    if df is None or df.empty:
        return {
            "status": "NO_DATA",
            "data_timestamp": pd.NaT,
            "data_age_hours": float('inf'),
            "failure_classification": "NO_DATA"
        }
    
    last_dt = df.index[-1]
    data_age_hours = (execution_timestamp - last_dt).total_seconds() / 3600.0
    
    return {
        "status": "FRESH", # Placeholder, to be updated after max_data_ts is known
        "data_timestamp": last_dt,
        "data_age_hours": data_age_hours,
        "failure_classification": "AVAILABLE"
    }

def evaluate_symbol_freshness(symbol_health: dict, max_data_ts: pd.Timestamp, expected_non_trading_day: bool):
    """Update symbol status based on max_data_ts."""
    for sym, health in symbol_health.items():
        if health["status"] == "FRESH":
            if health["data_timestamp"] < max_data_ts:
                health["status"] = "STALE"
                health["failure_classification"] = "UNRESOLVED" # Cannot determine if suspended or temporary provider failure
            else:
                health["status"] = "FRESH"
                health["failure_classification"] = "AVAILABLE"

def evaluate_aggregate_freshness(symbol_health: dict, execution_timestamp: pd.Timestamp, max_data_ts: pd.Timestamp) -> str:
    """Determine the aggregate session freshness."""
    statuses = [h["status"] for h in symbol_health.values()]
    
    if len(statuses) == 0:
        return "NO_DATA"
        
    all_stale = all(s == "STALE" for s in statuses)
    # If all symbols are 'FRESH' compared to max_data_ts, but max_data_ts is unexpectedly old
    # i.e., > 24 hours and not a weekend/holiday
    
    today = execution_timestamp.normalize()
    is_weekend = today.dayofweek >= 5
    is_premarket = execution_timestamp.hour < 15
    
    expected_delay = is_weekend or is_premarket
    
    # Check if max_data_ts itself is delayed
    max_data_age = (execution_timestamp - max_data_ts).total_seconds() / 3600.0
    if max_data_age > 24 and not expected_delay:
        return "DATA_DELAY"
        
    if all_stale:
        return "DATA_DELAY"
        
    has_stale = "STALE" in statuses
    has_missing = "NO_DATA" in statuses or "DOWNLOAD_ERROR" in statuses
    
    if has_stale and has_missing:
        return "PARTIAL_STALE" # Or PARTIAL_MISSING, precedence? We'll prioritize STALE. Actually, let's just use PARTIAL_STALE for both. Wait, "Case B: PARTIAL_STALE, Case C: PARTIAL_MISSING".
        
    if has_stale:
        return "PARTIAL_STALE"
    if has_missing:
        return "PARTIAL_MISSING"
        
    return "ALL_FRESH"

