import pandas as pd
import numpy as np
from pathlib import Path
import os
import yfinance as yf
from datetime import datetime, timedelta
import logging

import sys
sys.path.append("d:/stratergy")
from universe import get_universe
from run_forward_session import run_forward_session
from forward_config import get_frozen_forward_config
from forward_engine import RESULTS_DIR
from indicators.ema import wilder_style_ema
from indicators.rsi import wilder_rsi
from indicators.atr import wilder_atr

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_and_prepare_data(universe, end_date: pd.Timestamp):
    start_date = end_date - timedelta(days=150)
    
    symbols_expected = [u["symbol"] for u in universe]
    logging.info(f"Fetching data for {len(symbols_expected)} symbols from {start_date.date()} to {end_date.date()}")
    
    data = yf.download(symbols_expected, start=start_date.strftime("%Y-%m-%d"), end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"), group_by='ticker', auto_adjust=False, progress=False)
    
    day_data = {}
    prev_day_data = {}
    
    cfg = get_frozen_forward_config().strategy
    
    symbols_processed = []
    symbols_failed = []
    max_data_ts = pd.Timestamp("1970-01-01")
    
    for sym in symbols_expected:
        try:
            if len(symbols_expected) == 1:
                df = data.copy()
            else:
                if sym not in data.columns.levels[0]:
                    symbols_failed.append(sym)
                    continue
                df = data[sym].copy()
                
            df = df.dropna(subset=["Close"])
            if df.empty:
                symbols_failed.append(sym)
                continue
                
            symbols_processed.append(sym)
            
            # Freshness
            df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
            last_dt = df.index[-1]
            if last_dt > max_data_ts:
                max_data_ts = last_dt
                
            # Calculate indicators
            df["EMA"] = wilder_style_ema(df["Close"], cfg.ema_period)
            df["EMA_slope"] = df["EMA"].diff(cfg.slope_bars)
            df["RSI"] = wilder_rsi(df["Close"], cfg.rsi_period)
            
            df_lower = df.rename(columns={"High": "high", "Low": "low", "Close": "close"})
            df["ATR"] = wilder_atr(df_lower, cfg.atr_period)
            
            df["RSI_prev"] = df["RSI"].shift(1)
            df["signal"] = (
                (df["Close"] > df["EMA"]) &
                (df["EMA_slope"] > 0) &
                (df["RSI_prev"] < cfg.rsi_reclaim_level) &
                (df["RSI"] >= cfg.rsi_reclaim_level)
            )
            
            if end_date in df.index:
                row_today = df.loc[end_date]
                day_data[sym] = {
                    "Open": float(row_today["Open"]),
                    "High": float(row_today["High"]),
                    "Low": float(row_today["Low"]),
                    "Close": float(row_today["Close"]),
                    "Volume": float(row_today["Volume"])
                }
                
                prev_dates = df.index[df.index < end_date]
                if len(prev_dates) > 0:
                    prev_date = prev_dates[-1]
                    row_prev = df.loc[prev_date]
                    prev_day_data[sym] = {
                        "date": prev_date.strftime("%Y-%m-%d"),
                        "Open": float(row_prev["Open"]),
                        "High": float(row_prev["High"]),
                        "Low": float(row_prev["Low"]),
                        "Close": float(row_prev["Close"]),
                        "EMA": float(row_prev["EMA"]),
                        "EMA_slope": float(row_prev["EMA_slope"]),
                        "RSI": float(row_prev["RSI"]),
                        "ATR": float(row_prev["ATR"]),
                        "signal": bool(row_prev["signal"])
                    }
        except Exception as e:
            logging.error(f"Error processing {sym}: {e}")
            symbols_failed.append(sym)
            
    # Record universe health
    uni_health = {
        "date": end_date.strftime("%Y-%m-%d"),
        "symbols_expected": len(symbols_expected),
        "symbols_processed": len(symbols_processed),
        "symbols_failed": len(symbols_failed),
        "missing_symbols": ",".join(symbols_failed)
    }
    pd.DataFrame([uni_health]).to_csv(RESULTS_DIR / "forward_universe_health.csv", mode='a', header=not (RESULTS_DIR / "forward_universe_health.csv").exists(), index=False)
    
    return day_data, prev_day_data, max_data_ts, len(symbols_expected), len(symbols_processed), len(symbols_failed)

def generate_monthly_report(current_date: pd.Timestamp):
    trades_path = RESULTS_DIR / "forward_trades.csv"
    if not trades_path.exists(): return
    
    trades = pd.read_csv(trades_path)
    trades["exit_timestamp"] = pd.to_datetime(trades["exit_timestamp"])
    
    # Filter for current month
    month_trades = trades[(trades["exit_timestamp"].dt.year == current_date.year) & 
                          (trades["exit_timestamp"].dt.month == current_date.month)]
                          
    if month_trades.empty: return
    
    win_rate = (month_trades["net_pnl"] > 0).mean()
    avg_r = month_trades["r_multiple"].mean()
    med_r = month_trades["r_multiple"].median()
    expectancy_r = avg_r
    
    gross_profit = month_trades.loc[month_trades["net_pnl"] > 0, "net_pnl"].sum()
    gross_loss = abs(month_trades.loc[month_trades["net_pnl"] <= 0, "net_pnl"].sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    net_pnl = month_trades["net_pnl"].sum()
    total_costs = month_trades["transaction_costs"].sum()
    
    # Slippage
    entry_slip = ((month_trades["actual_entry"] - month_trades["planned_entry"]) / month_trades["planned_entry"] * 100)
    planned_exit = np.where(month_trades["exit_reason"].str.contains("TARGET"), month_trades["planned_target"], month_trades["planned_stop"])
    exit_slip = (abs(month_trades["actual_exit"] - planned_exit) / planned_exit * 100)
    round_trip_slip = entry_slip + exit_slip
    
    avg_entry_slip = entry_slip.mean()
    avg_exit_slip = exit_slip.mean()
    avg_round_trip = round_trip_slip.mean()
    worst_slip = round_trip_slip.max()
    
    gap_exits = month_trades["exit_reason"].str.contains("GAP").sum()
    ambig_exits = month_trades["exit_reason"].str.contains("AMBIGUITY").sum()
    
    content = f"""# Forward Monthly Report: {current_date.strftime('%Y-%m')}

## Trades
* completed trades: {len(month_trades)}
* wins: {(month_trades["net_pnl"] > 0).sum()}
* losses: {(month_trades["net_pnl"] <= 0).sum()}
* win rate: {win_rate:.2%}
* mean R: {avg_r:.2f}
* median R: {med_r:.2f}
* expectancy R: {expectancy_r:.2f}
* profit factor: {pf:.2f}
* net P&L: {net_pnl:.2f}
* transaction costs: {total_costs:.2f}

## Execution
* average entry slippage: {avg_entry_slip:.3f}%
* average exit slippage: {avg_exit_slip:.3f}%
* average round-trip slippage: {avg_round_trip:.3f}%
* worst slippage: {worst_slip:.3f}%
* gap exits: {gap_exits}
* same-bar stop/target events: {ambig_exits}
"""
    with open(RESULTS_DIR / f"forward_monthly_{current_date.strftime('%Y_%m')}.md", "w") as f:
        f.write(content)

def check_final_milestone():
    trades_path = RESULTS_DIR / "forward_trades.csv"
    if not trades_path.exists(): return
    
    trades = pd.read_csv(trades_path)
    completed = trades[trades["exit_timestamp"].notna()]
    if len(completed) >= 200:
        if not (RESULTS_DIR / "FORWARD_TEST_FINAL_REPORT.md").exists():
            with open(RESULTS_DIR / "FORWARD_TEST_FINAL_REPORT.md", "w") as f:
                f.write("# FORWARD TEST FINAL REPORT\n\nFORWARD RESULTS PENDING REVIEW\n")

def run_daily():
    execution_timestamp = pd.Timestamp.now()
    today = execution_timestamp.normalize()
    
    universe = get_universe()
    day_data, prev_day_data, max_data_ts, syms_exp, syms_proc, syms_fail = fetch_and_prepare_data(universe, today)
    
    status = "SUCCESS"
    reason = ""
    data_age = (execution_timestamp - max_data_ts).total_seconds() / 60.0 if max_data_ts != pd.Timestamp("1970-01-01") else 0
    
    if data_age > 1440: # 24 hours
        status = "DATA_DELAY"
    
    res = {}
    if len(day_data) == 0:
        if today.dayofweek >= 5:
            reason = "Expected: Weekend"
            status = "NO_MARKET_DATA"
        elif execution_timestamp.hour < 15:
            reason = "Expected: Market not closed"
            status = "NO_MARKET_DATA"
        else:
            reason = "Unexpected: Missing data"
            status = "NO_MARKET_DATA"
            from forward_watchdog import log_alert
            log_alert("WARNING", "DATA", reason, today.strftime("%Y-%m-%d"))
        logging.info(f"No market data for today. Reason: {reason}")
    else:
        logging.info(f"Running forward session for {today.strftime('%Y-%m-%d')}...")
        try:
            res = run_forward_session(today.strftime('%Y-%m-%d'), day_data, prev_day_data)
        except Exception as e:
            status = "RUNTIME_ERROR"
            reason = str(e)
            from forward_watchdog import log_alert
            log_alert("CRITICAL", "RUNTIME", reason, today.strftime("%Y-%m-%d"))
    
    # Run Watchdog
    from forward_watchdog import check_runner_health
    integrity_status = "PASS" if check_runner_health() else "INTEGRITY_FAILURE"
    
    if integrity_status == "INTEGRITY_FAILURE" and status == "SUCCESS":
        status = "INTEGRITY_FAILURE"
        
    # Generate Runner Health Log
    health_record = {
        "session_id": res.get("session_id", "N/A"),
        "execution_timestamp": execution_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduler_timestamp": execution_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "market_date": today.strftime("%Y-%m-%d"),
        "strategy_version": get_frozen_forward_config().strategy.__class__.__name__ + "_TPQSE_v1.0", # Simplified
        "universe_version": "CURRENT_ACTIVE_UNIVERSE",
        "symbols_expected": syms_exp,
        "symbols_processed": syms_proc,
        "symbols_failed": syms_fail,
        "data_timestamp": max_data_ts.strftime("%Y-%m-%d") if max_data_ts != pd.Timestamp("1970-01-01") else "N/A",
        "data_age_minutes": data_age,
        "signals_generated": res.get("signals_generated", 0),
        "entries_processed": res.get("entries_executed", 0),
        "exits_processed": res.get("exits_executed", 0),
        "open_positions": res.get("open_positions", 0),
        "ending_equity": res.get("ending_equity", 0),
        "integrity_status": integrity_status,
        "execution_status": status,
        "error_count": 1 if status in ["RUNTIME_ERROR", "INTEGRITY_FAILURE"] else 0,
        "warning_count": 1 if status == "DATA_DELAY" else 0
    }
    pd.DataFrame([health_record]).to_csv(RESULTS_DIR / "forward_runner_health.csv", mode='a', header=not (RESULTS_DIR / "forward_runner_health.csv").exists(), index=False)
    
    generate_monthly_report(today)
    check_final_milestone()

if __name__ == "__main__":
    run_daily()
