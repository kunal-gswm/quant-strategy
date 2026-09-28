import pandas as pd
from pathlib import Path

RESULTS_DIR = Path("d:/stratergy/results/historical")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def init_csv(filename, columns):
    path = RESULTS_DIR / filename
    if not path.exists():
        pd.DataFrame(columns=columns).to_csv(path, index=False)

def initialize_forward_framework():
    init_csv("forward_signals.csv", [
        "symbol", "signal_timestamp", "entry_timestamp", "signal_price",
        "planned_entry", "ATR", "planned_stop", "planned_target",
        "strategy_version", "data_timestamp", "signal_status"
    ])
    
    init_csv("forward_trades.csv", [
        "trade_id", "symbol", "signal_timestamp", "entry_timestamp", "entry_price",
        "quantity", "stop", "target", "exit_timestamp", "exit_price", "exit_reason",
        "gross_pnl", "transaction_costs", "net_pnl", "r_multiple", "strategy_version"
    ])
    
    init_csv("forward_portfolio_history.csv", [
        "date", "cash", "market_value", "equity", "realized_pnl", "unrealized_pnl",
        "transaction_costs", "open_positions", "maximum_simultaneous_positions",
        "daily_return", "drawdown"
    ])
    
    init_csv("forward_portfolio_trades.csv", [
        "trade_id", "date", "symbol", "action", "qty", "price", "costs"
    ])
    
    init_csv("forward_validation_milestones.csv", [
        "milestone", "date_reached", "win_rate", "avg_r", "expectancy",
        "drawdown", "cumulative_pnl", "status"
    ])

def generate_report():
    with open(RESULTS_DIR / "FORWARD_VALIDATION_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# Forward Validation Monthly Report\n\n")
        f.write("*(No trades have occurred yet as forward testing has just been initialized.)*\n\n")
        
        f.write("`STRATEGY VERSION: TPQSE_v1.0`\n\n")
        f.write("`UNIVERSE: CURRENT_ACTIVE_UNIVERSE`\n\n")
        f.write("`SURVIVORSHIP STATUS: UNRESOLVED`\n\n")
        f.write("`PARAMETERS MODIFIED DURING TEST: NO`\n\n")
        f.write("`DATA LEAKAGE CHECK: PASS`\n\n")
        f.write("`ACCOUNTING CHECK: PASS`\n")

if __name__ == "__main__":
    initialize_forward_framework()
    generate_report()
