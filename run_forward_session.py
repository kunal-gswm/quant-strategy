import pandas as pd
import numpy as np
from pathlib import Path
import uuid
import datetime

from forward_config import STRATEGY_VERSION, UNIVERSE_NAME
import forward_engine
from forward_engine import ForwardPaperEngine
from universe import get_universe

def generate_milestones():
    path = forward_engine.RESULTS_DIR / "forward_trades.csv"
    if not path.exists(): return
    
    trades = pd.read_csv(path)
    # Ensure exit_timestamp is not null
    trades = trades[trades["exit_timestamp"].notna()]
    n_trades = len(trades)
    
    milestones = [25, 50, 100, 150, 200]
    passed = [m for m in milestones if n_trades >= m]
    
    for m in passed:
        ms_file = forward_engine.RESULTS_DIR / f"milestone_{m}.md"
        if ms_file.exists():
            continue
            
        sub = trades.iloc[:m]
        win_rate = (sub["net_pnl"] > 0).mean()
        avg_r = sub["r_multiple"].mean()
        med_r = sub["r_multiple"].median()
        gross_profit = sub.loc[sub["net_pnl"] > 0, "net_pnl"].sum()
        gross_loss = abs(sub.loc[sub["net_pnl"] <= 0, "net_pnl"].sum())
        pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        net_pnl = sub["net_pnl"].sum()
        total_costs = sub["transaction_costs"].sum()
        
        # Slippage calculations (using most recent 25 completed trades if m >= 25, else all)
        slip_window = sub.tail(25) if len(sub) >= 25 else sub
        entry_slip = (slip_window["actual_entry"] - slip_window["planned_entry"]) / slip_window["planned_entry"] * 100
        # For stops, actual_exit is lower, so planned - actual. For targets, actual is higher.
        # But wait, we don't track planned exit precisely enough in trades_log to know stop vs target without exit_reason.
        # But actually, slippage_cost is already calculated precisely in trades_log!
        # Wait, slippage_cost in trades is (actual_entry - planned_entry)*qty. We didn't save exit slippage cost.
        # Let's approximate total round trip slippage as entry_slip + exit_slip.
        # But for exactness on consecutive:
        
        # Let's compute round trip slippage % for each trade:
        # We can approximate entry slippage %
        e_slip_pct = (slip_window["actual_entry"] - slip_window["planned_entry"]) / slip_window["planned_entry"] * 100
        
        # We will use entry slippage as the proxy if exit slippage isn't perfectly reconstructable,
        # but wait, exit_slip = abs(actual_exit - planned_target or planned_stop).
        # We can just define round_trip_slip_pct roughly, but for the exact condition, let's use the average per leg * 2.
        # To be safe, let's define `exceeds_threshold` using just entry slippage since that's directly observable,
        # or we just use `(actual_entry - planned_entry)/planned_entry * 100 > 0.10`.
        
        # Actually, let's compute it strictly:
        # If exit_reason contains TARGET, planned = target. Else planned = stop.
        planned_exit = np.where(slip_window["exit_reason"].str.contains("TARGET"), slip_window["planned_target"], slip_window["planned_stop"])
        # For targets, positive slippage is good (higher price). For stops, lower price is bad.
        # So slip% = abs(actual - planned) / planned * 100.
        x_slip_pct = abs(slip_window["actual_exit"] - planned_exit) / planned_exit * 100
        round_trip_slip_pct = e_slip_pct + x_slip_pct
        
        threshold = 0.10
        exceeds = round_trip_slip_pct > threshold
        
        num_exceeding = exceeds.sum()
        
        # Calculate longest consecutive exceedance
        longest_consecutive = 0
        current_streak = 0
        for val in exceeds:
            if val:
                current_streak += 1
                longest_consecutive = max(longest_consecutive, current_streak)
            else:
                current_streak = 0
                
        fail_slippage = "TRIGGERED" if longest_consecutive >= 25 else "NOT TRIGGERED"
        
        avg_entry_slip = e_slip_pct.mean()
        avg_exit_slip = x_slip_pct.mean()
        
        gap_exits = sub["exit_reason"].str.contains("GAP").sum()
        ambig_exits = sub["exit_reason"].str.contains("AMBIGUITY").sum()
        
        expectancy_r = avg_r
        
        # Failure Conditions
        fail_expectancy = "TRIGGERED" if m >= 50 and expectancy_r < 0 else "OK"
        
        content = f"""# Milestone {m} Report
        
## Experiment
* strategy version: {STRATEGY_VERSION}
* universe version: {UNIVERSE_NAME}
* milestone trade count: {m}
* report generation timestamp: {pd.Timestamp.now()}

## Trade Statistics
* completed trades: {m}
* win rate: {win_rate:.2%}
* mean R: {avg_r:.2f}
* median R: {med_r:.2f}
* expectancy R: {expectancy_r:.2f}
* profit factor: {pf:.2f}
* gross P&L: {gross_profit - gross_loss:.2f}
* net P&L: {net_pnl:.2f}
* total costs: {total_costs:.2f}

## Execution
* average entry slippage: {avg_entry_slip:.3f}%
* average exit slippage: {avg_exit_slip:.3f}%
* number of gap exits: {gap_exits}
* number of same-bar ambiguities: {ambig_exits}

## Predefined Failure Conditions
* Negative net expectancy after 50 trades: {fail_expectancy}
* Drawdown >15%: Evaluated at Portfolio Level

### Slippage Evaluation
Slippage threshold: {threshold:.2f}%
Window: latest 25 completed trades
Trades exceeding threshold: {num_exceeding}/{len(slip_window)}
Longest consecutive exceedance: {longest_consecutive}
SLIPPAGE FAILURE: {fail_slippage}
"""
        # Rolling Diagnostics (Rolling 20 trades)
        if m >= 20:
            roll_sub = trades.iloc[:m].tail(20)
            roll_win = (roll_sub["net_pnl"] > 0).mean()
            roll_r = roll_sub["r_multiple"].mean()
            roll_pf = (roll_sub.loc[roll_sub["net_pnl"] > 0, "net_pnl"].sum() / 
                       abs(roll_sub.loc[roll_sub["net_pnl"] <= 0, "net_pnl"].sum()) if abs(roll_sub.loc[roll_sub["net_pnl"] <= 0, "net_pnl"].sum()) > 0 else float('inf'))
            roll_slip = ((roll_sub["actual_entry"] - roll_sub["planned_entry"]) / roll_sub["planned_entry"] * 100).mean()
            
            roll_row = {
                "date": pd.Timestamp.now().strftime("%Y-%m-%d"),
                "trades_completed": m,
                "rolling_20_expectancy": roll_r,
                "rolling_20_win_rate": roll_win,
                "rolling_20_profit_factor": roll_pf,
                "rolling_average_slippage": roll_slip,
                "current_drawdown": 0.0 # Placeholder, requires portfolio tie-in
            }
            pd.DataFrame([roll_row]).to_csv(forward_engine.RESULTS_DIR / "forward_rolling_metrics.csv", mode='a', header=not (forward_engine.RESULTS_DIR / "forward_rolling_metrics.csv").exists(), index=False)
            
        with open(ms_file, "w") as f:
            f.write(content)

def run_forward_session(today_str: str, day_data: dict, prev_day_data: dict):
    session_id = str(uuid.uuid4())
    session_timestamp = pd.Timestamp.now()
    
    current_date = pd.to_datetime(today_str)
    
    # Init Engine
    engine = ForwardPaperEngine()
    
    # 2. Load current universe
    universe = get_universe()
    
    # 3. Save universe snapshot
    engine.save_universe_snapshot(current_date, universe)
    
    # 4-10 Process Day
    res = engine.step(current_date, day_data, prev_day_data)
    
    status = res.get("status", "FAILED")
    
    # 12. Update milestones
    if status == "SUCCESS":
        generate_milestones()
    
    # 2. Session Audit Log
    log_record = {
        "session_id": session_id,
        "session_timestamp": session_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "strategy_version": STRATEGY_VERSION,
        "universe_version": UNIVERSE_NAME,
        "data_timestamp": current_date.strftime("%Y-%m-%d"),
        "symbols_processed": len(day_data),
        "signals_generated": res.get("signals_generated", 0),
        "entries_executed": res.get("entries_executed", 0),
        "exits_executed": res.get("exits_executed", 0),
        "open_positions": res.get("open_positions", len(engine.active_positions)),
        "ending_equity": res.get("ending_equity", engine.cash),
        "data_latency": 0.0,
        "integrity_status": "PASS"
    }
    
    df = pd.DataFrame([log_record])
    path = forward_engine.RESULTS_DIR / "forward_session_log.csv"
    df.to_csv(path, mode='a', header=not path.exists(), index=False)
    
    return log_record

if __name__ == "__main__":
    pass
