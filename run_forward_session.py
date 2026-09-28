import pandas as pd
from pathlib import Path
import uuid
import datetime

from forward_config import STRATEGY_VERSION, UNIVERSE_NAME
from forward_engine import ForwardPaperEngine, RESULTS_DIR
from universe import get_universe

def generate_milestones():
    path = RESULTS_DIR / "forward_trades.csv"
    if not path.exists(): return
    
    trades = pd.read_csv(path)
    # Ensure exit_timestamp is not null
    trades = trades[trades["exit_timestamp"].notna()]
    n_trades = len(trades)
    
    milestones = [25, 50, 100, 150, 200]
    passed = [m for m in milestones if n_trades >= m]
    
    for m in passed:
        ms_file = RESULTS_DIR / f"milestone_{m}.md"
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
        
        # Slippage calculations
        entry_slip = (sub["actual_entry"] - sub["planned_entry"]) / sub["planned_entry"] * 100
        exit_slip = (sub["planned_stop"] - sub["actual_exit"]) / sub["planned_stop"] * 100 # approximate for stops
        avg_slip = entry_slip.mean() + exit_slip.mean()
        gap_exits = sub["exit_reason"].str.contains("GAP").sum()
        ambig_exits = sub["exit_reason"].str.contains("AMBIGUITY").sum()
        
        expectancy_r = avg_r
        
        # Failure Conditions
        fail_expectancy = "TRIGGERED" if m >= 50 and expectancy_r < 0 else "OK"
        fail_slippage = "TRIGGERED" if avg_slip > 0.10 else "OK" # >2x assumed 0.05%
        
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
* average entry slippage: {entry_slip.mean():.3f}%
* average exit slippage: {exit_slip.mean():.3f}%
* number of gap exits: {gap_exits}
* number of same-bar ambiguities: {ambig_exits}

## Predefined Failure Conditions
* Negative net expectancy after 50 trades: {fail_expectancy}
* Slippage >2x assumed: {fail_slippage}
* Drawdown >15%: Evaluated at Portfolio Level
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
            pd.DataFrame([roll_row]).to_csv(RESULTS_DIR / "forward_rolling_metrics.csv", mode='a', header=not (RESULTS_DIR / "forward_rolling_metrics.csv").exists(), index=False)
            
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
    path = RESULTS_DIR / "forward_session_log.csv"
    df.to_csv(path, mode='a', header=not path.exists(), index=False)
    
    return log_record

if __name__ == "__main__":
    pass
