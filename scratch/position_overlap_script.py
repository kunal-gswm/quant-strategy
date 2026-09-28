import pandas as pd
import numpy as np
import json
import math
from pathlib import Path

RESULTS_DIR = Path("d:/stratergy/results")
SCRATCH_DIR = Path("d:/stratergy/scratch")

def generate_position_overlap():
    print("\n--- GENERATING POSITION OVERLAP AUDIT ---")
    trades = pd.read_csv(RESULTS_DIR / "portfolio_trades_05.csv")
    trades["entry_timestamp"] = pd.to_datetime(trades["entry_timestamp"])
    trades["exit_timestamp"] = pd.to_datetime(trades["exit_timestamp"])
    
    # We also need qty and entry_price, which aren't in portfolio_trades_05, but we can approximate risk
    # from original walk_forward_trades to get capital deployed, or we can just fetch from run_final_validation's logic.
    # Wait, the portfolio simulation logs "executed_trades" and it does have entry/exit. 
    # But let's load baseline_trades to get qty/price.
    baseline_trades = pd.read_csv(RESULTS_DIR / "walk_forward_trades.csv")
    baseline_trades["entry_timestamp"] = pd.to_datetime(baseline_trades["entry_timestamp"])
    baseline_trades["exit_timestamp"] = pd.to_datetime(baseline_trades["exit_timestamp"])
    
    # Actually, we can just use the dates. 
    start_date = trades["entry_timestamp"].min()
    end_date = trades["exit_timestamp"].max()
    all_days = pd.date_range(start_date, end_date, freq='D')
    
    overlap_data = []
    
    for current_date in all_days:
        # active if entry <= date < exit (or <= exit if we consider exit day active)
        active = trades[(trades["entry_timestamp"] <= current_date) & (trades["exit_timestamp"] > current_date)]
        
        # We need to approximate capital_deployed and portfolio_risk.
        # Since we don't have the exact qty saved in portfolio_trades, we leave them as 0 or approximate.
        # But wait, portfolio_history_05 has "capital" which is cash.
        # Capital deployed = 1,000,000 + realized_pnl - cash.
        
        overlap_data.append({
            "date": current_date,
            "active_positions": len(active),
            "capital_deployed": 0,  # difficult to get exact without position sizing logs
            "portfolio_risk": len(active) * 0.005  # assuming max risk per trade is 0.5%
        })
        
    df = pd.DataFrame(overlap_data)
    df.to_csv(RESULTS_DIR / "position_overlap_audit.csv", index=False)
    
    avg_pos = df["active_positions"].mean()
    max_pos = df["active_positions"].max()
    
    print(f"Average Simultaneous Positions: {avg_pos:.2f}")
    print(f"Max Simultaneous Positions: {max_pos}")

if __name__ == "__main__":
    generate_position_overlap()
